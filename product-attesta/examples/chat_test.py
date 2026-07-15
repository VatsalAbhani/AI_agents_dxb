"""
Interactive test bench — YOU play the lead, live from your terminal.

Run:   python3 examples/chat_test.py
       LLM_PROVIDER=mock python3 examples/chat_test.py                       (LLM code path, offline)
       LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-... python3 examples/chat_test.py   (real AI)

Type messages as the lead. Every AI draft comes to you for approval first
(Enter = approve, e = edit, r = reject) — the exact flow a client's manager
will use. Blocked drafts show WHY and let you type a compliant rewrite.

Commands:  /status  — qualification so far      /quit — finish the session
On finish: the run is sealed + verified and a client-ready audit report is
written (chat_test_audit_report.md) — the artifact you show in a pitch.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.config import realestate_config                        # noqa: E402
from agent_template.conversation import ConversationalAgent                # noqa: E402
from agent_template.drafter import resolve_converser, drafter_mode         # noqa: E402

KEY, LEDGER, REPORT = "chat-test-key", "chat_test_run.jsonl", "chat_test_audit_report.md"

SAFE_REWRITE = ("I can't promise outcomes, but I'd be glad to share current listings and recent "
                "comparables so you can decide with full information.")


def ask(prompt):
    """input() that returns None on EOF so piped/aborted sessions end cleanly."""
    try:
        return input(prompt)
    except EOFError:
        return None


def approver(draft, ctx):
    print("\n  ┌─ DRAFT — needs your approval " + "─" * 34)
    for line in draft.split("\n"):
        print("  │ " + line)
    print("  └" + "─" * 64)
    choice = (ask("  [Enter]=approve · e=edit · r=reject > ") or "").strip().lower()
    if choice == "r":
        return {"decision": "reject", "by": "You (manager)"}
    if choice == "e":
        edited = (ask("  new text > ") or "").strip()
        return {"decision": "approve", "final": edited or draft, "by": "You (manager, edited)"}
    return {"decision": "approve", "final": draft, "by": "You (manager)"}


def remediator(draft, reasons, config):
    print("\n  🛡️  Guard BLOCKED the AI's draft:")
    for r in reasons:
        print(f"      ✗ {r['reason']}  [{r['id']}]")
    fixed = (ask("  compliant rewrite (Enter = standard safe reply) > ") or "").strip()
    return fixed or SAFE_REWRITE


def main():
    print("=" * 72)
    print("  LEADCODE GUARD · interactive agent test — you are the LEAD")
    print("=" * 72)
    company = (ask("Brokerage name [ABC Real Estate] > ") or "").strip() or "ABC Real Estate"
    name = (ask("Lead name [Test Lead] > ") or "").strip() or "Test Lead"

    config = realestate_config(company)
    agent = ConversationalAgent(config, converser=resolve_converser(config),
                                approver=approver, remediator=remediator)
    convo = agent.start({"name": name, "source": "chat-test", "enquiry": ""})

    print(f"\n[AI mode] {drafter_mode()}")
    print("Chat as the lead. /status shows qualification, /quit ends the session.")

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
        print(f"    known so far: {r['slots']}")

    out = agent.finalize(convo, key=KEY, path=LEDGER)
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
