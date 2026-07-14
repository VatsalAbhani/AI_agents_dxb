"""
Lead Follow-up Agent — per-client configuration.

This is what makes the agent a *product template*, not bespoke work: to deploy
for a new client you fill in a config (company, vertical, tone, rules) — you
don't rewrite code. The config also drives the Leadcode Guard policy set.
"""
from dataclasses import dataclass, field

from attesta.policy import Policy, default_policies


@dataclass
class ClientConfig:
    company: str
    vertical: str = "real_estate"            # real_estate | clinic | ...
    agent_name: str = "Lead Follow-up Agent"
    primary_channel: str = "whatsapp"
    tone: str = "warm, professional, concise"
    allowed_actions: list = field(default_factory=lambda: ["WhatsApp draft", "email draft", "CRM update"])
    blocked_actions: list = field(default_factory=lambda: ["payment links", "discounts", "ROI guarantees"])
    knowledge: dict = field(default_factory=dict)     # vertical facts (areas, services, hours…)
    extra_policies: list = field(default_factory=list)  # client-specific Policy objects


# vertical-specific guardrails layered on top of the default policy pack
VERTICAL_POLICIES = {
    "real_estate": [
        Policy("no-availability-guarantee", "require_approval",
               [r"available now", r"guaranteed availab", r"last unit"],
               "Availability/urgency claims need approval"),
    ],
    "clinic": [
        Policy("no-diagnosis", "block",
               [r"you (probably )?have\b", r"\bdiagnos", r"it'?s definitely"],
               "No diagnosis over chat"),
    ],
}


def build_policies(config: ClientConfig):
    """Default rules + vertical pack + client extras. Order is irrelevant (block wins)."""
    return default_policies() + VERTICAL_POLICIES.get(config.vertical, []) + list(config.extra_policies)


# ---- ready-made example configs (a real deployment starts by copying one) ----
def realestate_config(company="ABC Real Estate"):
    return ClientConfig(
        company=company, vertical="real_estate",
        knowledge={"areas": ["Downtown Dubai", "Dubai Marina", "JVC", "Business Bay", "Palm Jumeirah"]},
    )


def clinic_config(company="Aster Aesthetics"):
    return ClientConfig(
        company=company, vertical="clinic",
        primary_channel="whatsapp",
        knowledge={"services": ["consultation", "skin", "dental"], "hours": "9am–9pm"},
    )
