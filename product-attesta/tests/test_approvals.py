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
    submissions = []
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
        StubDashboard.submissions.append(payload)
        self._send(201, {"id": "d-1", "status": "pending"})

    def do_GET(self):
        self._send(200, {"id": "d-1", **StubDashboard.decision})

    def log_message(self, *a):  # silence
        pass


server = HTTPServer(("127.0.0.1", 0), StubDashboard)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"

print("\n== submits the draft with lead context ==")
approver = remote_approver(BASE, timeout=5, poll_every=0.05, quiet=True)
verdict = approver("Hello Rahul", {"lead": {"name": "Rahul"}})
ok("draft submitted", StubDashboard.submissions[0]["draft"] == "Hello Rahul")
ok("lead context included", StubDashboard.submissions[0]["lead"]["name"] == "Rahul")

print("\n== approval maps to gateway contract ==")
ok("decision approve", verdict["decision"] == "approve")
ok("final falls back to draft", verdict["final"] == "Hello Rahul")
ok("by is the manager", verdict["by"] == "Stub Mgr")

print("\n== edited approval returns the edited text ==")
StubDashboard.decision = {"status": "approved", "final": "Hello Rahul — edited", "by": "Mgr"}
verdict = approver("Hello Rahul", {})
ok("edited final wins", verdict["final"] == "Hello Rahul — edited")

print("\n== rejection maps to reject ==")
StubDashboard.decision = {"status": "rejected", "final": None, "by": "Mgr"}
verdict = approver("Bad draft", {})
ok("decision reject", verdict["decision"] == "reject")

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
