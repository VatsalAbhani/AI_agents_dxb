"""
End-to-end pilot: the conversational agent + the REAL approval dashboard.

1. Start the dashboard:   cd dashboard && npm run dev        (http://localhost:3005)
2. Run this script:       python examples/dashboard_pilot.py
3. Open http://localhost:3005/approvals (phone or laptop) and approve/edit/reject
   each draft as it appears. The agent waits for your decision, then continues —
   and the whole conversation lands in the Attesta ledger as usual.

Set DASHBOARD_URL / GUARD_API_KEY env vars to point elsewhere.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.approvals import remote_approver                     # noqa: E402
from agent_template.config import realestate_config                      # noqa: E402
from agent_template.conversation import ConversationalAgent              # noqa: E402
from agent_template.drafter import resolve_converser, drafter_mode, make_variants  # noqa: E402

BASE = os.getenv("DASHBOARD_URL", "http://localhost:3005")
KEY = os.getenv("GUARD_API_KEY", "demo-key")


def main():
    print("=" * 72)
    print("  LEADCODE GUARD · agent + live approval dashboard")
    print(f"  dashboard: {BASE}/approvals   ·   [AI mode] {drafter_mode()}")
    print("=" * 72)

    config = realestate_config("ABC Real Estate")
    agent = ConversationalAgent(
        config,
        converser=resolve_converser(config),
        approver=remote_approver(BASE, api_key=KEY, client=config.company,
                                 variants=make_variants(config)),
        remediator=lambda d, r, c: ("I can't promise outcomes, but I'd gladly share current "
                                    "listings and comparables so you can decide."),
    )
    convo = agent.start({"name": "Rahul Mehta", "source": "Meta Ads",
                         "enquiry": "interested in a Dubai apartment"})

    for msg in [
        "Hi — looking for a 2-bed in Dubai Marina.",
        "Budget around 2.4 million, mainly investment.",
    ]:
        print(f"\n👤 Lead: {msg}")
        r = agent.reply(convo, msg)
        if r["status"] == "sent":
            print(f"🤖 Agent [{r['tier']} · {r['action']['type']}] → SENT:\n    {r['reply']}")
        else:
            print(f"🤖 [{r['tier']}] → {r['status'].upper()} — nothing sent.")

    out = agent.finalize(convo, key="dashboard-pilot-key", path="dashboard_pilot_run.jsonl")
    print("\n" + "=" * 72)
    print(f"[Attesta]  {out['entries']} actions · integrity: {'INTACT ✓' if out['intact'] else 'FAILED ✗'}")
    print(f"[Ledger]   dashboard_pilot_run.jsonl")
    print("=" * 72)


if __name__ == "__main__":
    main()
