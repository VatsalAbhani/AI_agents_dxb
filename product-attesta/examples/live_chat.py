"""
Live chat + live dashboard — YOU type the lead's messages, approvals happen
in the browser (or on a phone).

1. Start the dashboard:   cd dashboard && npm run dev      (http://localhost:3005)
2. Run this script:       python3 examples/live_chat.py
3. Type messages as the lead. Each AI draft appears on the dashboard;
   the agent waits until you Approve / Edit / Reject there, then continues.

The conversation keeps going until you type /quit — then the run is sealed,
verified, and the audit report is written. Set DASHBOARD_URL / GUARD_API_KEY
env vars to point elsewhere. Tip: open the dashboard on your phone via the
"Network:" URL that `npm run dev` prints — that's the real pilot experience.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.approvals import remote_approver                     # noqa: E402
from agent_template.config import realestate_config                      # noqa: E402
from agent_template.conversation import ConversationalAgent              # noqa: E402
from agent_template.drafter import resolve_converser, drafter_mode       # noqa: E402

BASE = os.getenv("DASHBOARD_URL", "http://localhost:3005")
KEY = os.getenv("GUARD_API_KEY", "demo-key")
LEDGER, REPORT = "live_chat_run.jsonl", "live_chat_audit_report.md"


def ask(prompt):
    try:
        return input(prompt)
    except EOFError:
        return None


def main():
    print("=" * 72)
    print("  LEADCODE GUARD · live chat — you are the LEAD, approvals on the dashboard")
    print(f"  dashboard: {BASE}/approvals   ·   [AI mode] {drafter_mode()}")
    print("=" * 72)
    company = (ask("Brokerage name [ABC Real Estate] > ") or "").strip() or "ABC Real Estate"
    name = (ask("Lead name [Test Lead] > ") or "").strip() or "Test Lead"
    rel = (ask("Relationship (new/returning/referral) [new] > ") or "").strip().lower() or "new"

    config = realestate_config(company)
    agent = ConversationalAgent(
        config,
        converser=resolve_converser(config),
        approver=remote_approver(BASE, api_key=KEY, client=company),
        remediator=lambda d, r, c: ("I can't promise outcomes, but I'd gladly share current "
                                    "listings and comparables so you can decide."),
    )
    convo = agent.start({"name": name, "source": "live-chat", "relationship": rel, "enquiry": ""})
    print("\nChat as the lead. Each draft waits for a decision on the dashboard.")
    print("/status shows qualification, /quit ends the session.")

    while True:
        msg = ask("\n👤 You (lead) > ")
        if msg is None or msg.strip() == "/quit":
            break
        msg = msg.strip()
        if not msg:
            continue
        if msg == "/status":
            print(f"    tier={convo.tier} · escalated={convo.escalated} · known={convo.slots}")
            continue

        r = agent.reply(convo, msg)
        tag = f"{r['tier']} · {r['action']['type']}" + (" · ESCALATED" if r["escalated"] else "")
        if r["status"] == "sent":
            print(f"\n🤖 Agent [{tag}] → SENT:")
            for line in r["reply"].split("\n"):
                print("    " + line)
        else:
            print(f"\n🤖 [{tag}] → {r['status'].upper()} — nothing was sent to the lead.")

    out = agent.finalize(convo, key="live-chat-key", path=LEDGER)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(out["report"])
    q = out["qualification"]
    print("\n" + "=" * 72)
    print(f"[Qualification]  tier={q['tier']} · escalated={q['escalated']} · slots={q['slots']}")
    print(f"[Attesta]        {out['entries']} recorded actions · integrity: {'INTACT ✓' if out['intact'] else 'FAILED ✗'}")
    print(f"[Artifacts]      ledger: {LEDGER} · audit report: {REPORT}")
    print("=" * 72)


if __name__ == "__main__":
    main()
