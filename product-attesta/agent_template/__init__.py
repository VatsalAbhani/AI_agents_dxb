"""
Lead Follow-up Agent — a productized, per-client AI agent built on Attesta Core
+ Leadcode Guard. Deploy for a new client by writing a ClientConfig; flip on a
real LLM with environment variables (see drafter.resolve_drafter).
"""
from .agent import LeadFollowupAgent
from .config import ClientConfig, build_policies, clinic_config, realestate_config
from .drafter import (
    build_system_prompt, drafter_mode, make_llm_drafter, promo_drafter,
    resolve_drafter, template_drafter,
)

__all__ = [
    "LeadFollowupAgent", "ClientConfig", "build_policies",
    "realestate_config", "clinic_config",
    "template_drafter", "promo_drafter", "make_llm_drafter",
    "resolve_drafter", "drafter_mode", "build_system_prompt",
]
