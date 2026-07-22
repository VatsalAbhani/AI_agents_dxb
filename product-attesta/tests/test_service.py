"""
Tests for the agent service:  python tests/test_service.py
Runs the real service + a stub dashboard on local threads. Stdlib only.
Covers: intake -> guarded turn -> approval -> state, restart survival
(DB + evidence chain), close/seal/verify, auth.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["APPROVAL_TIMEOUT"] = "15"
os.environ["APPROVAL_POLL"] = "0.1"

from service.server import create_server            # noqa: E402
from attesta.verifier import verify as verify_ledger  # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


# ---- stub dashboard: auto-approves every draft -----------------------
class StubDash(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        self.rfile.read(length)
        self._send(201, {"id": "stub-1", "status": "pending"})

    def do_GET(self):
        self._send(200, {"id": "stub-1", "status": "approved", "final": None, "by": "Stub Mgr"})

    def log_message(self, *a):
        pass


dash = HTTPServer(("127.0.0.1", 0), StubDash)
threading.Thread(target=dash.serve_forever, daemon=True).start()
DASH_URL = f"http://127.0.0.1:{dash.server_address[1]}"

DATA = tempfile.mkdtemp(prefix="guard-service-test-")
KEY = "test-key"


def start_service():
    srv = create_server(port=0, data_dir=DATA, dashboard_url=DASH_URL, api_key=KEY)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def call(base, method, path, body=None, key=KEY):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"content-type": "application/json", "x-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def wait_turns(base, cid, n, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, state = call(base, "GET", f"/leads/{cid}")
        agent_turns = [t for t in state["turns"] if t["role"] == "agent"]
        if len(agent_turns) >= n:
            return state
        time.sleep(0.2)
    return call(base, "GET", f"/leads/{cid}")[1]


srv1, base1 = start_service()

print("\n== auth + health ==")
code, _ = call(base1, "GET", "/leads", key="wrong")
ok("bad api key -> 401", code == 401)
with urllib.request.urlopen(base1 + "/health", timeout=5) as r:
    ok("health endpoint answers", json.loads(r.read())["ok"] is True)

print("\n== intake -> guarded turn -> approved reply ==")
code, out = call(base1, "POST", "/leads", {
    "name": "Rahul", "source": "Meta Ads", "relationship": "new",
    "message": "hi, looking for a 2 bed in dubai marina",
})
ok("lead created (201)", code == 201 and "id" in out)
cid = out["id"]
state = wait_turns(base1, cid, 1)
agent_turns = [t for t in state["turns"] if t["role"] == "agent"]
ok("agent replied via stub approval", agent_turns and agent_turns[0]["status"] == "sent")
ok("qualification persisted", state["slots"].get("area") == "Dubai Marina")

print("\n== second message accumulates state ==")
call(base1, "POST", f"/leads/{cid}/message", {"text": "budget 2.4m, mainly investment"})
state = wait_turns(base1, cid, 2)
ok("two agent turns", len([t for t in state["turns"] if t["role"] == "agent"]) == 2)
ok("slots accumulate across turns", state["slots"].get("budget") == 2400000.0
   and state["slots"].get("purpose") == "invest")

print("\n== RESTART: state and evidence chain survive ==")
srv1.shutdown()
srv2, base2 = start_service()
call(base2, "POST", f"/leads/{cid}/message", {"text": "cash buyer, need it this month"})
state = wait_turns(base2, cid, 3)
ok("third turn after restart", len([t for t in state["turns"] if t["role"] == "agent"]) == 3)
ok("history retained across restart", state["tier"] == "Hot" and state["escalated"] is True)
ledger_path = os.path.join(DATA, "ledgers", f"{cid}.jsonl")
entries = [json.loads(l) for l in open(ledger_path) if l.strip() and "_seal" not in l]
ok("single unbroken chain on disk", entries[0]["prev_hash"] == "0" * 64
   and all(entries[i]["prev_hash"] == entries[i - 1]["entry_hash"] for i in range(1, len(entries))))

print("\n== lead chat page + report endpoint ==")
import urllib.request as _ur
def raw_get(url):
    try:
        with _ur.urlopen(url, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

code2, body2 = raw_get(base2 + f"/chat?key={KEY}")
ok("chat page serves with key", code2 == 200 and "Start a conversation" in body2)
code2, _b = raw_get(base2 + "/chat?key=wrong")
ok("chat page 403 without key", code2 == 403)
code2, _b = raw_get(base2 + f"/leads/{cid}/report?key={KEY}")
ok("report 409 before close", code2 == 409)

print("\n== close: seal + verify + report ==")
code, out = call(base2, "POST", f"/leads/{cid}/close")
ok("close returns INTACT", code == 200 and out["intact"] is True)
ok("audit report written", os.path.exists(out["report"]))
v = verify_ledger(ledger_path, key=os.getenv("LEDGER_KEY", "pilot-ledger-key"))
ok("ledger verifies independently", v["intact"] is True)
code2, body2 = raw_get(base2 + f"/leads/{cid}/report?key={KEY}")
ok("report downloadable after close", code2 == 200 and "INTACT" in body2)
call(base2, "POST", f"/leads/{cid}/message", {"text": "one more thing"})
time.sleep(0.8)
_, state = call(base2, "GET", f"/leads/{cid}")
ok("closed conversations take no more agent turns",
   len([t for t in state["turns"] if t["role"] == "agent"]) == 3)

srv2.shutdown()
dash.shutdown()
shutil.rmtree(DATA, ignore_errors=True)
print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
