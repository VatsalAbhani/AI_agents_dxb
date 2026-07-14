"""
Lead Follow-up Agent — the productized unit.

One reusable class that, for any client config:
  1. receives a lead,
  2. has the AI draft a reply (recorded to Attesta),
  3. runs it through Leadcode Guard (policy check + human approval),
  4. auto-requests a compliant rewrite if a hard policy blocks it,
  5. sends only after it's cleared, and
  6. records every step into the tamper-evident ledger for the audit report.

Attesta Core stays the engine underneath — this is the sellable application on top.
"""
from attesta.gateway import Gateway
from attesta.recorder import Recorder
from attesta.redact import redact_pii
from attesta.report import audit_report
from attesta.verifier import verify

from .config import build_policies
from .drafter import template_drafter


def _stub_sender(channel):
    """Demo tool. In production this is your WhatsApp Business API / email / CRM client."""
    def send(message):
        return {"channel": channel, "delivered": True, "chars": len(message)}
    return send


class LeadFollowupAgent:
    def __init__(self, config, drafter=None, approver=None, remediator=None,
                 sender=None, redactor=redact_pii):
        self.config = config
        self.drafter = drafter or template_drafter
        self.remediator = remediator            # produce a compliant rewrite when a draft is blocked
        self.rec = Recorder("record", redactor=redactor)   # the Attesta evidence engine
        self.gate = Gateway(self.rec, policies=build_policies(config), approver=approver)
        self.sender = sender or _stub_sender(config.primary_channel)
        self.results = []

    def process(self, lead, drafter=None):
        d = drafter or self.drafter
        ch = self.config.primary_channel
        self.rec.event("lead", "received", {"lead": lead})
        draft = self.rec.llm("draft", lambda _l: d(_l, self.config), lead)

        res = self.gate.send(ch, draft, self.sender, context={"lead": lead})

        if res["status"] == "blocked" and self.remediator:
            self.rec.event("remediation", "requested", {"reasons": res["reasons"]})
            fixed = self.remediator(draft, res["reasons"], self.config)
            fixed = self.rec.llm("redraft", lambda _old: fixed, draft)   # record the corrected draft
            res = self.gate.send(ch, fixed, self.sender, context={"lead": lead})

        self.results.append({"lead": lead.get("name"), "status": res["status"]})
        return res

    def process_batch(self, leads):
        return [self.process(lead) for lead in leads]

    def finalize(self, key=None, path="pilot_run.jsonl", period="[period]"):
        self.rec.ledger.seal(key)
        self.rec.ledger.save(path)
        v = verify(path, key=key)
        report = audit_report(path, key=key, client=self.config.company,
                              agent=self.config.agent_name, period=period)
        return {"intact": v["intact"], "entries": v["entries"],
                "report": report, "path": path, "results": self.results}
