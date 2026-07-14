"""
Real-estate pilot — the productized Lead Follow-up Agent, deployed for one client.

Run:  python examples/realestate_pilot.py

This is what a paid pilot looks like end to end: configure the brokerage, feed a
batch of real leads, let the AI draft + Guard approve/block + auto-remediate, then
hand the client a verified audit report. Swap `template_drafter` for a real LLM
(make_llm_drafter) and the stub sender for the WhatsApp Business API to go live.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.agent import LeadFollowupAgent               # noqa: E402
from agent_template.config import realestate_config              # noqa: E402
from agent_template.drafter import promo_drafter, resolve_drafter, drafter_mode  # noqa: E402

KEY = "abc-realestate-key"
PATH = "pilot_run.jsonl"


# --- the client's people/tools (stubs for the demo) ---
def manager_approves(draft, context):
    # a real approval queue; here the manager approves compliant drafts as-is
    return {"decision": "approve", "final": draft, "by": "Manager · ABC Real Estate"}


def manager_rewrites(draft, reasons, config):
    # when Guard blocks a draft, produce a compliant replacement
    return ("Hi! Thanks for your interest. Some Downtown Dubai units have seen strong demand "
            "historically, though future performance can't be promised — and I can't offer "
            "discounts here. I'd be glad to share genuine current options: ready or off-plan?")


def main():
    print("=" * 70)
    print("  ABC REAL ESTATE · AI Lead Follow-up Agent (pilot)")
    print("  productized template · powered by Leadcode Guard + Attesta Core")
    print("=" * 70)

    config = realestate_config("ABC Real Estate")
    print(f"\n[AI drafting mode] {drafter_mode()}")
    agent = LeadFollowupAgent(config, drafter=resolve_drafter(config),
                              approver=manager_approves, remediator=manager_rewrites)

    leads = [
        {"name": "Rahul Mehta", "phone": "+971 50 123 4567", "source": "Meta Ads",
         "area": "Downtown Dubai", "budget": "AED 2.5M", "enquiry": "2BR, ready to move"},
        {"name": "Sarah Collins", "phone": "+971 55 987 6543", "source": "Website",
         "area": "Dubai Marina", "budget": "AED 1.8M", "enquiry": "1BR investment"},
        {"name": "Wang Lei", "phone": "+971 52 111 2222", "source": "Property Finder",
         "area": "JVC", "budget": "AED 900k", "enquiry": "studio, high yield"},
    ]

    print("\n[Processing real leads]")
    for lead in leads:
        res = agent.process(lead)
        print(f"    {lead['name']:<14} {lead['area']:<16} → {res['status'].upper()}")

    print("\n[A lead where the AI got too salesy — Guard should catch it]")
    risky = {"name": "Ahmed Investor", "phone": "+971 50 777 8888", "source": "Instagram",
             "area": "Business Bay", "budget": "AED 3M", "enquiry": "will it make money?"}
    res = agent.process(risky, drafter=promo_drafter)
    print(f"    {risky['name']:<14} {risky['area']:<16} → {res['status'].upper()} "
          "(blocked, rewritten by manager, then sent)")

    out = agent.finalize(key=KEY, path=PATH, period="July 2026")
    open("pilot_audit_report.md", "w").write(out["report"])

    print(f"\n[Result]  ledger: {out['entries']} actions · integrity: "
          f"{'INTACT ✓' if out['intact'] else 'FAILED'} · report → pilot_audit_report.md")
    print("\n[Audit report — summary section]")
    grab = False
    for ln in out["report"].splitlines():
        if ln.startswith("## Summary"):
            grab = True
        elif ln.startswith("## Timeline"):
            break
        if grab:
            print("    " + ln)

    print("\n" + "=" * 70)
    print("Sold as: 'AI lead follow-up for your brokerage — with approval + audit.'")
    print("Underneath: Attesta Core — the verifiable-evidence engine you scale later.")
    print("=" * 70)


if __name__ == "__main__":
    main()
