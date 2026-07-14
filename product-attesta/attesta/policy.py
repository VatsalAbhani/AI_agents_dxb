"""
Attesta — the policy engine (part of the Leadcode Guard control layer).

Simple, transparent rules an operator understands: block outright, or require
human approval. This is deliberately NOT "AI governance" — it's the safety
controls a business owner asks for ("the AI must not promise guaranteed returns,
and nothing goes out without approval").
"""
import re


class Policy:
    def __init__(self, id, kind, patterns, reason):
        assert kind in ("block", "require_approval")
        self.id = id
        self.kind = kind
        self.patterns = [re.compile(p, re.I) for p in patterns]
        self.reason = reason

    def hit(self, text):
        return any(p.search(text or "") for p in self.patterns)


def default_policies():
    """A starter set — extend per client. Order doesn't matter; block wins."""
    return [
        Policy("no-guaranteed-returns", "block",
               [r"guarantee", r"\bguaranteed\b", r"\d+\s*%\s*(roi|return|apprec|growth)"],
               "No guaranteed investment returns"),
        Policy("no-medical-claims", "block",
               [r"\bcure\b", r"guaranteed results", r"no side ?effects", r"100%\s*safe"],
               "No medical/treatment guarantees"),
        Policy("no-unapproved-discount", "require_approval",
               [r"discount", r"\d+\s*%\s*off", r"special price", r"free upgrade"],
               "Discounts require approval"),
        Policy("no-sensitive-data-request", "require_approval",
               [r"passport", r"emirates ?id", r"bank details", r"\biban\b", r"card number"],
               "Requesting sensitive data requires approval"),
        Policy("approval-before-send", "require_approval", [r".+"],
               "Human approval required before sending"),
    ]


def evaluate(text, policies=None):
    policies = policies or default_policies()
    blocks = [p for p in policies if p.kind == "block" and p.hit(text)]
    if blocks:
        return {"decision": "block",
                "reasons": [{"id": p.id, "reason": p.reason} for p in blocks]}
    appr = [p for p in policies if p.kind == "require_approval" and p.hit(text)]
    if appr:
        return {"decision": "needs_approval",
                "reasons": [{"id": p.id, "reason": p.reason} for p in appr]}
    return {"decision": "allow", "reasons": []}
