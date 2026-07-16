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
    # relationship sensitivity: these lead types are DRAFT-ONLY — the bot never
    # sends to them; approved text goes to the assigned human advisor
    draft_only_relationships: list = field(default_factory=lambda: ["returning", "referral", "personal"])


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
        knowledge={
            "areas": ["Downtown Dubai", "Dubai Marina", "JVC", "Business Bay", "Palm Jumeirah"],
            # the units the agent may recommend — it only ever grounds replies in this list
            "inventory": [
                {"name": "Marina Vista", "area": "Dubai Marina", "bedrooms": 2, "price": 2_300_000, "type": "ready"},
                {"name": "Downtown Ace", "area": "Downtown Dubai", "bedrooms": 2, "price": 2_700_000, "type": "ready"},
                {"name": "Creek Palace", "area": "Dubai Creek Harbour", "bedrooms": 1, "price": 1_450_000, "type": "off-plan"},
                {"name": "JVC Gardens", "area": "Jumeirah Village Circle", "bedrooms": 1, "price": 850_000, "type": "ready"},
            ],
        },
    )


def clinic_config(company="Aster Aesthetics"):
    return ClientConfig(
        company=company, vertical="clinic",
        primary_channel="whatsapp",
        knowledge={"services": ["consultation", "skin", "dental"], "hours": "9am–9pm"},
    )
