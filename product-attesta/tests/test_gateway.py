"""
Tests for the hardened core + Leadcode Guard layer:
  python tests/test_gateway.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attesta.recorder import Recorder, ReplayDivergence, REPLAY_UNAVAILABLE  # noqa: E402
from attesta.replay import replay                                            # noqa: E402
from attesta.redact import redact_pii                                        # noqa: E402
from attesta.policy import evaluate                                          # noqa: E402
from attesta.gateway import Gateway                                          # noqa: E402
from attesta.verifier import verify                                         # noqa: E402
from attesta.ledger import Ledger, canon, sha                               # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


print("\n== side-effect-safe replay (the fix) ==")
CALLED = {"live": 0}


def spy_tool(x):
    CALLED["live"] += 1        # must NEVER run during replay
    return {"x": x}


def agent(rec, city, extra=False):
    rec.tool("weather", spy_tool, city)
    if extra:
        rec.tool("weather", spy_tool, city)     # unexpected call on replay


rec = Recorder("record")
agent(rec, "Dubai")
ok("record made 1 live call", CALLED["live"] == 1)

CALLED["live"] = 0
rep = replay(agent, rec.ledger, "Dubai", extra=True)     # extra call not in recording
ok("replay made ZERO live calls (side-effect-safe)", CALLED["live"] == 0)
ok("extra call flagged as divergence", any(d["kind"] == "extra_call" for d in rep["divergences"]))

print("\n== strict replay raises ==")
raised = False
try:
    replay_rec = Recorder("replay", ledger=rec.ledger, strict=True)
    agent(replay_rec, "AbuDhabi")     # different input -> divergence -> raise
except ReplayDivergence:
    raised = True
ok("strict mode raises ReplayDivergence", raised)

print("\n== redaction keeps integrity ==")
r2 = Recorder("record", redactor=redact_pii)
r2.event("lead", "in", {"phone": "+971 50 123 4567", "email": "a@b.com", "note": "2BR Downtown"})
import tempfile  # noqa: E402
path = os.path.join(tempfile.gettempdir(), "attesta_redact.jsonl")
r2.ledger.seal("k")
r2.ledger.save(path)
stored = open(path).read()
ok("phone is redacted in storage", "50 123 4567" not in stored and "[phone]" in stored)
ok("email is redacted in storage", "a@b.com" not in stored)
ok("redacted ledger still verifies intact", verify(path, key="k")["intact"] is True)

print("\n== policy engine ==")
ok("guaranteed ROI is blocked", evaluate("guaranteed to appreciate 20% return")["decision"] == "block")
ok("normal message needs approval", evaluate("Thanks for your enquiry")["decision"] == "needs_approval")
ok("discount needs approval", evaluate("I can give you a 10% discount")["decision"] == "needs_approval")

print("\n== gateway blocks, approves, records ==")
rec3 = Recorder("record")
SENT = {"n": 0}


def real_send(msg):
    SENT["n"] += 1
    return {"ok": True}


gate = Gateway(rec3, approver=lambda d, c: {"decision": "approve", "final": d, "by": "mgr@x.ae"})
blocked = gate.send("whatsapp", "guaranteed 20% ROI, 100% safe", real_send)
ok("risky message blocked", blocked["status"] == "blocked")
ok("blocked message NOT sent", SENT["n"] == 0)
sent = gate.send("whatsapp", "Thanks, shall I share options?", real_send)
ok("approved message sent", sent["status"] == "sent" and SENT["n"] == 1)
ok("gateway recorded policy + approval + send events",
   any(e["type"] == "policy" for e in rec3.ledger.entries)
   and any(e["type"] == "approval" for e in rec3.ledger.entries)
   and any(e["type"] == "gateway" and e["name"] == "sent" for e in rec3.ledger.entries))

print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
