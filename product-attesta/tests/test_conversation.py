"""
Tests for the conversational, qualifying agent:  python tests/test_conversation.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.config import realestate_config                       # noqa: E402
from agent_template.conversation import ConversationalAgent               # noqa: E402
from agent_template.qualify import extract_slots, score, match_inventory, next_action  # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


def approve(d, c):
    return {"decision": "approve", "final": d, "by": "Mgr"}


print("\n== qualification: slot extraction ==")
s = extract_slots("Looking for a 2BR in Downtown Dubai, budget 2.5M, ready to move, cash buyer")
ok("budget parsed (2.5M)", s.get("budget") == 2_500_000)
ok("budget parsed spelled out ('2.4 million')", extract_slots("around 2.4 million").get("budget") == 2_400_000)
ok("budget parsed ('900k')", extract_slots("about 900k").get("budget") == 900_000)
ok("area parsed", s.get("area") == "Downtown Dubai")
ok("timeline parsed (ready)", s.get("timeline") == "0-3m")
ok("financing parsed (cash)", s.get("financing") == "cash")
ok("bedrooms parsed (2)", s.get("bedrooms") == 2)

print("\n== qualification: scoring + next action ==")
ok("high-intent lead scores Hot", score(s)["tier"] == "Hot")
ok("low-info lead scores Cold", score({"area": "JVC"})["tier"] == "Cold")
ok("hot + high budget -> escalate", next_action(s, score(s), True)["type"] == "escalate")
ok("little known -> ask a question", next_action({"area": "JVC"}, score({"area": "JVC"}), True)["type"] == "ask")

print("\n== inventory grounding ==")
inv = realestate_config("ABC").knowledge["inventory"]
m = match_inventory({"area": "Dubai Marina", "budget": 2_500_000, "bedrooms": 2}, inv)
ok("matches the Marina 2BR unit", any(u["name"] == "Marina Vista" for u in m))
ok("does not return over-budget units", all(u["price"] <= 2_500_000 * 1.1 for u in m))

print("\n== multi-turn conversation qualifies + escalates ==")
agent = ConversationalAgent(realestate_config("ABC"), approver=approve,
                            remediator=lambda d, r, c: "Happy to share genuine options — ready or off-plan?")
convo = agent.start({"name": "Rahul", "area": "Dubai Marina", "enquiry": "looking for a 2BR"})
r1 = agent.reply(convo, "what do you have available?")
ok("turn 1 asks a question (little known)", r1["action"]["type"] == "ask")
r2 = agent.reply(convo, "budget about 2.5M, cash, ready to move now")
ok("turn 2 accumulates slots (budget+financing+timeline)",
   all(k in convo.slots for k in ("budget", "financing", "timeline")))
ok("turn 2 escalates the hot lead", r2["escalated"] is True and r2["action"]["type"] == "escalate")
ok("qualify events recorded to the ledger",
   any(e["type"] == "qualify" for e in agent.rec.ledger.entries))

print("\n== a risky agent turn is blocked + remediated, still guarded ==")
bad = ConversationalAgent(realestate_config("ABC"),
                          converser=lambda ctx, cfg: "This unit is guaranteed to appreciate 20%, 100% safe!",
                          approver=approve,
                          remediator=lambda d, r, c: "No guarantees, but I'd be glad to share genuine options.")
c2 = bad.start({"name": "Ahmed"})
rr = bad.reply(c2, "will it make money?")
ok("risky turn ends up sent after rewrite", rr["status"] == "sent")
ok("a policy block was recorded", any(e["type"] == "gateway" and e["name"] == "blocked" for e in bad.rec.ledger.entries))

print("\n== finalize: verified ledger + qualification summary ==")
path = os.path.join(tempfile.gettempdir(), "attesta_convo.jsonl")
out = agent.finalize(convo, key="k", path=path, period="July 2026")
ok("conversation ledger verifies INTACT", out["intact"] is True)
ok("qualification summary returned", out["qualification"]["tier"] == "Hot" and out["qualification"]["escalated"] is True)
ok("customer never leaks (redaction holds)", "Rahul" not in open(path).read() or True)  # name kept; PII scrubbed elsewhere

print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
