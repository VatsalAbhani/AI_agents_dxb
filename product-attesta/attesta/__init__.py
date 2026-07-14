"""Attesta — the flight recorder for AI agents.

Attesta Core: verifiable, tamper-evident action ledger + deterministic replay
(the infrastructure). On top of it, a Gateway + Policy control layer turns it
into a sellable product ("Leadcode Guard") that approves and proves what agents
do before they act.
"""
from .gateway import Gateway
from .ledger import Ledger
from .policy import Policy, default_policies, evaluate
from .recorder import Recorder, ReplayDivergence
from .redact import redact_pii
from .replay import replay
from .report import audit_csv, audit_report
from .verifier import verify

__version__ = "0.2.0"
__all__ = [
    "Ledger", "Recorder", "ReplayDivergence", "replay", "verify",
    "Gateway", "Policy", "default_policies", "evaluate",
    "redact_pii", "audit_report", "audit_csv", "__version__",
]
