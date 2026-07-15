"""
Conversational Lead Follow-up Agent — the upgraded, multi-turn agent.

Instead of one blind reply, it holds a real back-and-forth: on each incoming
message it updates what it knows about the lead (qualification), grounds its
answer in the brokerage's actual inventory, decides the next step (ask a
question / share options / escalate to a human), and — as always — runs every
outgoing message through Leadcode Guard (policy + approval) and records the whole
conversation into the Attesta tamper-evident ledger.
"""
from dataclasses import dataclass, field

from attesta.gateway import Gateway
from attesta.recorder import Recorder
from attesta.redact import redact_pii
from attesta.report import audit_report
from attesta.verifier import verify

from .agent import _stub_sender
from .config import build_policies
from .drafter import template_converse
from .qualify import extract_slots, match_inventory, next_action, score


@dataclass
class Conversation:
    lead: dict
    slots: dict = field(default_factory=dict)
    history: list = field(default_factory=list)   # [{role: 'lead'|'agent', text}]
    tier: str = "Cold"
    escalated: bool = False


class ConversationalAgent:
    def __init__(self, config, converser=None, approver=None, remediator=None,
                 sender=None, redactor=redact_pii):
        self.config = config
        self.converser = converser or template_converse
        self.remediator = remediator
        self.rec = Recorder("record", redactor=redactor)
        self.gate = Gateway(self.rec, policies=build_policies(config), approver=approver)
        self.sender = sender or _stub_sender(config.primary_channel)

    def start(self, lead):
        seed = {}
        if lead.get("area"):
            seed["area"] = lead["area"]
        if lead.get("budget"):
            seed = extract_slots(str(lead["budget"]), seed)
        seed = extract_slots(lead.get("enquiry", ""), seed)
        self.rec.event("lead", "received", {"lead": lead})
        return Conversation(lead=lead, slots=seed)

    def reply(self, convo, message, converser=None):
        ch = self.config.primary_channel
        drafter = converser or self.converser
        # 1) record + understand the incoming message
        self.rec.event("lead", "message", {"text": message})
        convo.history.append({"role": "lead", "text": message})
        convo.slots = extract_slots(message, convo.slots)

        # 2) qualify + decide the next step
        sc = score(convo.slots)
        convo.tier = sc["tier"]
        inventory = self.config.knowledge.get("inventory", [])
        matches = match_inventory(convo.slots, inventory)
        action = next_action(convo.slots, sc, bool(matches))
        if action["type"] == "escalate":
            convo.escalated = True
        self.rec.event("qualify", "update", {
            "tier": sc["tier"], "score": sc["score"], "slots": convo.slots,
            "action": action["type"], "matches": [u.get("name") for u in matches],
        })

        # 3) draft the next message (grounded), then run it through the gateway
        ctx = {"lead": convo.lead, "slots": convo.slots, "history": convo.history,
               "matches": matches, "action": action, "score": sc}
        draft = self.rec.llm("draft", lambda c: drafter(c, self.config), ctx)
        res = self.gate.send(ch, draft, self.sender, context={"lead": convo.lead})
        was_blocked = res["status"] == "blocked"
        if was_blocked and self.remediator:
            self.rec.event("remediation", "requested", {"reasons": res["reasons"]})
            fixed = self.remediator(draft, res["reasons"], self.config)
            fixed = self.rec.llm("redraft", lambda _o: fixed, draft)
            res = self.gate.send(ch, fixed, self.sender, context={"lead": convo.lead})

        # only what was actually sent enters the conversation history — a blocked
        # draft must not pollute later turns' context or masquerade as a reply
        final = res.get("final")
        if final:
            convo.history.append({"role": "agent", "text": final})
        return {"reply": final, "status": res["status"], "blocked": was_blocked, "tier": convo.tier,
                "action": action, "escalated": convo.escalated, "slots": dict(convo.slots)}

    def finalize(self, convo=None, key=None, path="conversation_run.jsonl", period="[period]"):
        self.rec.ledger.seal(key)
        self.rec.ledger.save(path)
        v = verify(path, key=key)
        out = {"intact": v["intact"], "entries": v["entries"], "path": path,
               "report": audit_report(path, key=key, client=self.config.company,
                                      agent=self.config.agent_name, period=period)}
        if convo is not None:
            out["qualification"] = {"tier": convo.tier, "slots": convo.slots, "escalated": convo.escalated}
        return out
