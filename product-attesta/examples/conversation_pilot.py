"""
Conversational Lead Follow-up Agent — the upgraded demo.

Run:  python examples/conversation_pilot.py   (LLM_PROVIDER=mock to use the LLM code path)

Watch a real back-and-forth: the agent qualifies the lead over several turns,
grounds its answers in the brokerage's actual inventory, and escalates the hot
lead to a human — while Leadcode Guard catches an over-enthusiastic draft mid-
conversation and every message is recorded into Attesta's tamper-evident ledger.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.config import realestate_config                       # noqa: E402
from agent_template.conversation import ConversationalAgent               # noqa: E402
from agent_template.drafter import resolve_converser, drafter_mode        # noqa: E402

KEY, PATH = "abc-convo-key", "conversation_run.jsonl"


def manager_approves(draft, ctx):
    return {"decision": "approve", "final": draft, "by": "Manager · ABC Real Estate"}


def manager_rewrites(draft, reasons, config):
    return ("Historically, some Dubai Marina units have performed well, though future results can't be "
            "promised. I'd be glad to share recent comparables so you can judge for yourself — shall I?")


# an intentionally over-enthusiastic draft, to show Guard catching it mid-conversation
def over_eager(ctx, config):
    return "Absolutely — this unit is guaranteed to appreciate 20% and it's a 100% safe investment!"


def show(role, text, tag=""):
    who = "👤 Lead" if role == "lead" else "🤖 Agent"
    print(f"\n{who}{(' ['+tag+']') if tag else ''}:")
    for line in text.split("\n"):
        print("    " + line)


def main():
    print("=" * 72)
    print("  ABC REAL ESTATE · Conversational AI Lead Agent (with qualification)")
    print("  powered by Leadcode Guard + Attesta Core")
    print("=" * 72)
    print(f"\n[AI mode] {drafter_mode()}")

    config = realestate_config("ABC Real Estate")
    agent = ConversationalAgent(config, converser=resolve_converser(config),
                                approver=manager_approves, remediator=manager_rewrites)

    lead = {"name": "Rahul Mehta", "phone": "+971 50 123 4567", "source": "Meta Ads",
            "enquiry": "interested in a Dubai apartment"}
    convo = agent.start(lead)
    print(f"\n[New lead from {lead['source']}] {lead['name']}")

    turns = [
        ("Hi, I saw your ad — I'm looking for a 2-bed apartment in Dubai Marina.", None),
        ("My budget is around 2.4 million, mainly to invest.", None),
        ("Is it a good investment? Will I actually make money?", over_eager),   # Guard should catch the draft
        ("Sounds fair. I can pay cash and want to close this quarter.", None),
    ]

    for msg, override in turns:
        show("lead", msg)
        r = agent.reply(convo, msg, converser=override)
        tag = f"{r['tier']} · {r['action']['type']}"
        if r["blocked"]:
            print("\n    🛡️  Guard BLOCKED the AI's draft (false-promise) → manager rewrote a compliant version →")
        if r["escalated"]:
            tag += " · ESCALATED"
        show("agent", r["reply"], tag)

    out = agent.finalize(convo, key=KEY, path=PATH, period="July 2026")
    q = out["qualification"]
    print("\n" + "=" * 72)
    print(f"[Qualification]  tier={q['tier']}  ·  escalated={q['escalated']}")
    print(f"[Known so far]   {q['slots']}")
    print(f"[Attesta]        {out['entries']} actions · integrity: {'INTACT ✓' if out['intact'] else 'FAILED'}")
    print(f"[Privacy]        raw phone stored? {'NO ✓' if '50 123 4567' not in open(PATH).read() else 'yes'}")
    print("=" * 72)
    print("One AI conversation: qualified the lead, stayed on-policy, grounded every")
    print("suggestion in real inventory, escalated the hot buyer — all provable.")
    print("=" * 72)


if __name__ == "__main__":
    main()
