"""
Leadcode Guard — the business demo (powered by Attesta Core).

Run:  python examples/leadcode_guard_demo.py

Scenario a Dubai real-estate brokerage understands instantly: a lead comes in,
an AI drafts the WhatsApp reply, the GATEWAY policy-checks it, a human approves
(or edits) BEFORE it sends, and Attesta records every action into a tamper-
evident ledger that produces an audit report — and can be independently verified.

  Leadcode Guard  = what you sell (safety, approval, proof)
  Attesta Core    = the engine underneath (the verifiable-evidence infrastructure)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attesta.gateway import Gateway            # noqa: E402
from attesta.recorder import Recorder          # noqa: E402
from attesta.redact import redact_pii          # noqa: E402
from attesta.report import audit_report        # noqa: E402
from attesta.verifier import verify            # noqa: E402
from attesta.ledger import Ledger              # noqa: E402
import json                                    # noqa: E402

KEY = "leadcode-demo-key"
LEDGER = "leadcode_run.jsonl"

AGENT_PROFILE = {
    "agent": "Lead Follow-up Agent",
    "owner": "ABC Real Estate (Downtown Dubai)",
    "purpose": "Reply to inbound property leads",
    "allowed": ["WhatsApp draft", "email draft", "CRM update"],
    "not_allowed": ["payment links", "discounts", "ROI guarantees"],
    "approval": "Human approval required before sending",
    "risk": "Medium",
}


# ---- the "AI agent" (drafts) and the real tool (the send) ----
def draft_reply(kind):
    good = ("Thank you for your enquiry about a 2-bedroom in Downtown Dubai around AED 2.5M. "
            "May I confirm whether you'd prefer a ready unit or off-plan?")
    risky = ("Great choice! This unit is guaranteed to appreciate 20% in the first year — "
             "a 100% safe investment.")
    return risky if kind == "risky" else good


def whatsapp_send(message):        # the real side-effecting tool
    return {"channel": "whatsapp", "delivered": True, "chars": len(message)}


# ---- a stand-in "human manager" approver ----
def manager(draft, context):
    # edits the risky compliant, approves the good one as-is
    if "guaranteed" in draft.lower() or "100% safe" in draft.lower():
        fixed = ("Some Downtown Dubai units have seen strong historical demand, though future "
                 "performance can't be promised. Happy to share recent comparables — ready or off-plan?")
        return {"decision": "edit", "final": fixed, "by": "Manager · ABC Real Estate"}
    return {"decision": "approve", "final": draft, "by": "Manager · ABC Real Estate"}


def bar():
    print("=" * 70)


def main():
    bar()
    print("  LEADCODE GUARD  ·  AI lead follow-up with approval + audit")
    print("  (powered by Attesta Core — the verifiable-evidence engine)")
    bar()

    print("\n[Agent registry]")
    for k, v in AGENT_PROFILE.items():
        print(f"    {k:>11}: {v}")

    # Attesta core: record everything, redact PII in what we store
    rec = Recorder("record", redactor=redact_pii)
    gate = Gateway(rec, approver=manager)

    lead = {"name": "Rahul Mehta", "phone": "+971 50 123 4567",
            "source": "Meta Ads", "enquiry": "2BR Downtown Dubai, budget AED 2.5M"}
    rec.event("lead", "received", {"lead": lead})
    print(f"\n[1] Lead received: {lead['enquiry']}  (from {lead['source']})")

    # message 1 — clean draft
    d1 = draft_reply("good")
    rec.event("llm", "draft", {"text": d1})
    print("\n[2] AI drafted reply #1 → running through the gateway...")
    r1 = gate.send("whatsapp", d1, whatsapp_send, context={"lead": lead})
    print(f"    policy: needs approval → manager {('approved' if r1['status']=='sent' else r1['status'])} → {r1['status'].upper()}")

    # message 2 — risky draft (blocked by policy, then human-corrected)
    d2 = draft_reply("risky")
    rec.event("llm", "draft", {"text": d2})
    print("\n[3] AI drafted reply #2: \"...guaranteed to appreciate 20%... 100% safe...\"")
    r2 = gate.send("whatsapp", d2, whatsapp_send, context={"lead": lead})
    print(f"    policy: {r2['status'].upper()}  (blocked: {[x['reason'] for x in r2.get('reasons', [])]})")
    if r2["status"] == "blocked":
        # human rewrites a compliant version and re-sends through the gateway
        v = manager(d2, {"lead": lead})
        r3 = gate.send("whatsapp", v["final"], whatsapp_send, context={"lead": lead})
        print(f"    → manager rewrote a compliant message → {r3['status'].upper()}")

    # seal + save (Attesta core)
    rec.ledger.seal(KEY)
    rec.ledger.save(LEDGER)

    # verify integrity (the $1B core)
    vres = verify(LEDGER, key=KEY)
    print(f"\n[4] Attesta integrity check → {'INTACT ✓' if vres['intact'] else 'FAILED'}  "
          f"({len(rec.ledger.entries)} actions, merkle={vres['merkle_root'][:16]}...)")

    # audit report (what the client pays for)
    report = audit_report(LEDGER, key=KEY, client="ABC Real Estate",
                          agent="Lead Follow-up Agent", period="July 2026")
    open("leadcode_audit_report.md", "w").write(report)
    print("\n[5] Audit report written → leadcode_audit_report.md  (preview):")
    for ln in report.splitlines()[:14]:
        print("    " + ln)

    # prove PII was redacted in storage
    stored = open(LEDGER).read()
    print("\n[6] Privacy: raw phone stored?",
          "NO ✓ (redacted)" if "50 123 4567" not in stored else "yes")

    # tamper demo (the moat)
    lines = [l for l in open(LEDGER).read().splitlines() if l.strip()]
    forged = []
    done = False
    for l in lines:
        o = json.loads(l)
        if not done and o.get("type") == "gateway" and o.get("name") == "sent":
            o["payload"]["final"] = "FORGED MESSAGE"
            done = True
        forged.append(json.dumps(o, sort_keys=True, separators=(",", ":")))
    open("leadcode_tampered.jsonl", "w").write("\n".join(forged) + "\n")
    vt = verify("leadcode_tampered.jsonl", key=KEY)
    print(f"[7] Someone edits a sent message in the log → verify: "
          f"{'TAMPER DETECTED ✓' if not vt['intact'] else 'missed'}")

    bar()
    print("Sold as safety + approval + proof. Underneath: Attesta's verifiable")
    print("evidence engine — the same core that scales to the agent-trust rail.")
    bar()


if __name__ == "__main__":
    main()
