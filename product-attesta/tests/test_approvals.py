"""
Tests for the remote approver (dashboard client):  python tests/test_approvals.py
Runs a stub of the dashboard API on a local thread — no dependencies.
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.approvals import remote_approver  # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


class StubDashboard(BaseHTTPRequestHandler):
    """Configurable stub: records submissions, serves a scripted decision."""
    decision = {"status": "approved", "final": None, "by": "Stub Mgr"}
    get_script = []          # optional per-request GET responses (popped in order)
    submissions = []
    variants_received = []
    require_key = "demo-key"

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.headers.get("x-api-key") != self.require_key:
            return self._send(401, {"error": "bad key"})
        length = int(self.headers.get("content-length", 0))
        payload = json.loads(self.rfile.read(length))
        if self.path.endswith("/variants"):
            StubDashboard.variants_received.append(payload)
            return self._send(200, {"ok": True})
        StubDashboard.submissions.append(payload)
        self._send(201, {"id": "d-1", "status": "pending"})

    def do_GET(self):
        if StubDashboard.get_script:
            return self._send(200, {"id": "d-1", **StubDashboard.get_script.pop(0)})
        self._send(200, {"id": "d-1", **StubDashboard.decision})

    def log_message(self, *a):  # silence
        pass


server = HTTPServer(("127.0.0.1", 0), StubDashboard)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"

print("\n== submits the draft with lead context ==")
approver = remote_approver(BASE, timeout=5, poll_every=0.05, quiet=True)
verdict = approver("Hello Rahul", {"lead": {"name": "Rahul"},
                                   "intent": {"tier": "Hot", "high_intent": True},
                                   "relationship": "new"})
ok("draft submitted", StubDashboard.submissions[0]["draft"] == "Hello Rahul")
ok("lead context included", StubDashboard.submissions[0]["lead"]["name"] == "Rahul")
ok("intent forwarded", StubDashboard.submissions[0]["intent"]["high_intent"] is True)
ok("relationship forwarded", StubDashboard.submissions[0]["relationship"] == "new")

print("\n== approval maps to gateway contract ==")
ok("decision approve", verdict["decision"] == "approve")
ok("final falls back to draft", verdict["final"] == "Hello Rahul")
ok("by is the manager", verdict["by"] == "Stub Mgr")

print("\n== edited approval returns the edited text ==")
StubDashboard.decision = {"status": "approved", "final": "Hello Rahul — edited", "by": "Mgr"}
verdict = approver("Hello Rahul", {})
ok("edited final wins", verdict["final"] == "Hello Rahul — edited")

print("\n== rejection maps to reject, reason passes through ==")
StubDashboard.decision = {"status": "rejected", "final": None, "by": "Mgr", "reason": "wrong unit quoted"}
verdict = approver("Bad draft", {})
ok("decision reject", verdict["decision"] == "reject")
ok("reason passes through", verdict.get("reason") == "wrong unit quoted")

print("\n== on-demand variants: manager asks, agent generates, choice flows back ==")
StubDashboard.get_script = [
    {"status": "pending", "variants_requested": True, "has_variants": False},
    {"status": "pending", "variants_requested": True, "has_variants": True},
    {"status": "approved", "final": "Concise alt.", "by": "Mgr", "variant": 0},
]
vapprover = remote_approver(BASE, timeout=5, poll_every=0.05, quiet=True,
                            variants=lambda d, c: ["Concise alt.", "Warmer alt."])
verdict = vapprover("Original draft text", {})
ok("variants posted to the dashboard once",
   len(StubDashboard.variants_received) == 1
   and StubDashboard.variants_received[0]["variants"] == ["Concise alt.", "Warmer alt."])
ok("chosen variant text becomes the final", verdict["final"] == "Concise alt.")
ok("variant index passes through", verdict.get("variant") == 0)

print("\n== fail-closed behaviour ==")
StubDashboard.decision = {"status": "pending"}
verdict = remote_approver(BASE, timeout=0.3, poll_every=0.05, quiet=True)("Slow", {})
ok("timeout -> reject (fail closed)", verdict["decision"] == "reject" and "timeout" in verdict["by"])

verdict = remote_approver("http://127.0.0.1:1", timeout=1, poll_every=0.05, quiet=True)("X", {})
ok("unreachable server -> reject (fail closed)", verdict["decision"] == "reject")

print("\n== bad api key -> reject (fail closed) ==")
verdict = remote_approver(BASE, api_key="wrong", timeout=1, poll_every=0.05, quiet=True)("X", {})
ok("401 -> reject", verdict["decision"] == "reject")

server.shutdown()
print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
