"""
Attesta — the gateway (the "sit between the agent and the tools" control layer).

This is what makes Attesta sellable to a business owner: instead of only logging
after the fact, the gateway runs the policy check and (if needed) human approval
BEFORE the real action executes — and records every step into the Attesta
tamper-evident ledger. Block, approve, prove.

    agent draft ─▶ Gateway ─▶ policy check ─▶ approval (if needed) ─▶ tool executes
                        └────────────── every step recorded to Attesta ──────────────┘
"""
from .policy import default_policies, evaluate


class Gateway:
    def __init__(self, recorder, policies=None, approver=None):
        self.rec = recorder                       # Attesta Recorder (the evidence engine)
        self.policies = policies or default_policies()
        self.approver = approver                  # callable(draft, context) -> verdict dict

    def send(self, channel, draft, execute, context=None):
        """Guard an outbound action. `execute` is the real tool (only called if allowed)."""
        context = context or {}
        decision = evaluate(draft, self.policies)
        self.rec.event("policy", "check", {
            "channel": channel, "draft": draft,
            "decision": decision["decision"], "reasons": decision["reasons"],
        })

        if decision["decision"] == "block":
            self.rec.event("gateway", "blocked",
                           {"channel": channel, "draft": draft, "reasons": decision["reasons"]})
            return {"status": "blocked", "reasons": decision["reasons"], "final": None}

        final = draft
        approved_by = None
        if decision["decision"] == "needs_approval":
            if self.approver is None:
                self.rec.event("gateway", "held_for_approval", {"channel": channel, "draft": draft})
                return {"status": "held_for_approval", "final": None}
            verdict = self.approver(draft, context)   # {"decision","final","by"[,"reason"]}
            payload = {
                "channel": channel, "by": verdict.get("by"),
                "final": verdict.get("final", draft), "edited": verdict.get("final", draft) != draft,
            }
            if verdict.get("reason"):
                payload["reason"] = verdict["reason"]   # why the human edited/rejected
            if verdict.get("variant") is not None:
                payload["variant"] = verdict["variant"]  # which alternative the human chose
            self.rec.event("approval", verdict.get("decision", "approve"), payload)
            if verdict.get("decision") == "reject":
                return {"status": "rejected", "by": verdict.get("by"), "final": None}
            final = verdict.get("final", draft)
            approved_by = verdict.get("by")

        # execute the real action ONLY after policy + approval, and record it
        result = self.rec.tool(f"{channel}_send", execute, final)
        self.rec.event("gateway", "sent",
                       {"channel": channel, "final": final, "approved_by": approved_by})
        return {"status": "sent", "final": final, "approved_by": approved_by, "result": result}
