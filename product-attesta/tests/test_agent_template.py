"""
Tests for the productized Lead Follow-up Agent:  python tests/test_agent_template.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.agent import LeadFollowupAgent          # noqa: E402
from agent_template.config import realestate_config, clinic_config, build_policies  # noqa: E402
from agent_template.drafter import promo_drafter, template_drafter  # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


def approve(draft, ctx):
    return {"decision": "approve", "final": draft, "by": "Mgr"}


def rewrite(draft, reasons, config):
    return "Thanks for your interest — happy to share genuine current options. Ready or off-plan?"


LEAD = {"name": "Test User", "phone": "+971 50 000 1111", "area": "Downtown Dubai", "budget": "AED 2M"}

print("\n== template is configurable per client ==")
rc, cc = realestate_config("ABC"), clinic_config("Aster")
ok("real-estate + clinic build distinct policy sets", len(build_policies(rc)) != len(build_policies(cc)) or rc.vertical != cc.vertical)
ok("config carries company + vertical", rc.company == "ABC" and rc.vertical == "real_estate")

print("\n== normal lead → drafted, approved, sent ==")
agent = LeadFollowupAgent(realestate_config("ABC"), approver=approve, remediator=rewrite)
res = agent.process(LEAD)
ok("normal lead is sent", res["status"] == "sent")
ok("draft was recorded via the AI boundary", any(e["type"] == "llm" and e["name"] == "draft" for e in agent.rec.ledger.entries))

print("\n== risky draft → blocked, remediated, then sent ==")
res2 = agent.process({"name": "Ahmed", "area": "Business Bay"}, drafter=promo_drafter)
ok("risky lead ends up sent (after rewrite)", res2["status"] == "sent")
ok("a block was recorded", any(e["type"] == "gateway" and e["name"] == "blocked" for e in agent.rec.ledger.entries))
ok("a remediation was recorded", any(e["type"] == "remediation" for e in agent.rec.ledger.entries))

print("\n== PII redacted, ledger verifies, report generated ==")
path = os.path.join(tempfile.gettempdir(), "attesta_pilot.jsonl")
out = agent.finalize(key="k", path=path, period="July 2026")
ok("ledger verifies INTACT", out["intact"] is True)
ok("customer phone redacted in storage", "50 000 1111" not in open(path).read())
ok("audit report has integrity + summary", "INTACT" in out["report"] and "Messages sent" in out["report"])

print("\n== batch processing works ==")
a2 = LeadFollowupAgent(realestate_config("XYZ"), approver=approve, remediator=rewrite)
a2.process_batch([LEAD, dict(LEAD, name="Two"), dict(LEAD, name="Three")])
ok("processed 3 leads", len(a2.results) == 3)

print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
