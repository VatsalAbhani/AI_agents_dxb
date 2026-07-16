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


def _advisor_sender(channel):
    """Sender for relationship leads: the approved text is handed to the assigned
    human advisor to send personally — the bot never delivers it."""
    def send(text):
        return {"status": "routed_to_advisor", "channel": channel,
                "note": "relationship lead — approved text handed to the assigned advisor to send personally"}
    return send


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
        high_intent = action["type"] == "escalate"
        first_escalation = high_intent and not convo.escalated
        if high_intent:
            convo.escalated = True
        self.rec.event("qualify", "update", {
            "tier": sc["tier"], "score": sc["score"], "slots": convo.slots,
            "action": action["type"], "matches": [u.get("name") for u in matches],
        })
        # the handoff clock starts here: from this entry's timestamp to the human
        # decision is the "high-intent signal -> human takeover" pilot metric
        if first_escalation:
            self.rec.event("handoff", "requested", {
                "reason": action.get("reason", "high-intent lead"),
                "tier": sc["tier"], "slots": convo.slots,
            })

        # relationship sensitivity: returning/referral/personal leads are DRAFT-ONLY —
        # the approved text is routed to the assigned human advisor, never bot-sent
        relationship = (convo.lead.get("relationship") or "new").lower()
        draft_only = relationship in self.config.draft_only_relationships
        sender = _advisor_sender(ch) if draft_only else self.sender
        send_ctx = {"lead": convo.lead, "relationship": relationship,
                    "intent": {"tier": sc["tier"], "action": action["type"],
                               "high_intent": high_intent}}

        # 3) draft the next message (grounded), then run it through the gateway
        ctx = {"lead": convo.lead, "slots": convo.slots, "history": convo.history,
               "matches": matches, "action": action, "score": sc}
        draft = self.rec.llm("draft", lambda c: drafter(c, self.config), ctx)
        res = self.gate.send(ch, draft, sender, context=send_ctx)
        was_blocked = res["status"] == "blocked"
        if was_blocked and self.remediator:
            self.rec.event("remediation", "requested", {"reasons": res["reasons"]})
            fixed = self.remediator(draft, res["reasons"], self.config)
            fixed = self.rec.llm("redraft", lambda _o: fixed, draft)
            res = self.gate.send(ch, fixed, sender, context=send_ctx)

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
