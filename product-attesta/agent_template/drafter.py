"""
Lead Follow-up Agent — the drafter (the "AI brain" that writes the reply).

Pluggable by design:
  * template_drafter  — deterministic, offline, no API key (demos/tests)
  * make_llm_drafter  — a REAL LLM (OpenAI / Anthropic / OpenAI-compatible),
                        or provider="mock" to exercise the LLM code path offline
  * promo_drafter     — an intentionally over-enthusiastic draft, to show Guard
                        catching a policy violation
  * resolve_drafter   — pick the right drafter from environment variables

Whatever the drafter produces still passes through Leadcode Guard (policy +
approval) before it can be sent — the AI is never trusted blindly. And the
model is briefed with the SAME rules Guard enforces (defense in depth).

Go live:  export LLM_PROVIDER=openai  OPENAI_API_KEY=sk-...  LLM_MODEL=gpt-4o-mini
Test the wiring offline:  export LLM_PROVIDER=mock
"""
import json
import os

LAST_LLM_ERROR = None   # set when a real call fails and we fall back (for debugging)


# ---- deterministic drafters (no network) ----------------------------
def template_drafter(lead, config):
    name = lead.get("name", "there")
    if config.vertical == "real_estate":
        area = lead.get("area") or ""
        budget = lead.get("budget", "")
        parts = [f"Hi {name}, thanks for your enquiry"]
        if area:
            parts.append(f"about {area}")
        if budget:
            parts.append(f"(budget {budget})")
        return (" ".join(parts) + ". Would you prefer a ready unit or off-plan? "
                "I can share a few matching options and recent comparables.")
    if config.vertical == "clinic":
        return (f"Hi {name}, thanks for reaching out to {config.company}. "
                "Could you share a preferred date and time so we can arrange your consultation?")
    return f"Hi {name}, thanks for your message — how can we help?"


def promo_drafter(lead, config):
    """Simulates an AI that got too salesy — Guard should block this."""
    return (f"Hi {lead.get('name', 'there')}! Amazing timing — this unit is guaranteed to appreciate 20% "
            "and it's a 100% safe investment. I can also give you a 10% discount if you sign today!")


# ---- prompt built from the client's OWN guardrails ------------------
def build_system_prompt(config):
    from .config import build_policies
    rules = []
    for p in build_policies(config):
        verb = "NEVER" if p.kind == "block" else "Only with human approval —"
        rules.append(f"- {verb} {p.reason.lower()}")
    return (f"You are the {config.agent_name} for {config.company} (a {config.vertical} business). "
            f"Tone: {config.tone}. Write a short, friendly first reply to the inbound lead and ask exactly "
            f"one clarifying question. Do not invent specific prices, availability, or facts. "
            f"Follow these rules exactly:\n" + "\n".join(rules))


# ---- request/response plumbing (pure, so it's unit-testable) ---------
def build_request(provider, system, user, api_key, model, base_url):
    if provider == "anthropic":
        return {
            "url": "https://api.anthropic.com/v1/messages",
            "headers": {"content-type": "application/json", "x-api-key": api_key or "",
                        "anthropic-version": "2023-06-01"},
            "body": {"model": model or "claude-sonnet-5", "max_tokens": 300,
                     "system": system, "messages": [{"role": "user", "content": user}]},
        }
    base = (base_url or "https://api.openai.com/v1").rstrip("/")
    return {
        "url": base + "/chat/completions",
        "headers": {"content-type": "application/json", "authorization": "Bearer " + (api_key or "")},
        "body": {"model": model or "gpt-4o-mini", "max_tokens": 300,
                 "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
    }


def parse_response(provider, data):
    if provider == "anthropic":
        c = (data or {}).get("content") or [{}]
        return (c[0].get("text") or "").strip()
    ch = ((data or {}).get("choices") or [{}])[0]
    return ((ch.get("message") or {}).get("content") or "").strip()


def _mock_answer(lead, config):
    name, area, budget = lead.get("name", "there"), lead.get("area", ""), lead.get("budget", "")
    return (f"Hi {name}, thanks so much for reaching out to {config.company}! "
            + (f"I'd be glad to help you find the right home in {area}" if area else "I'd be glad to help with your search")
            + (f" within your {budget} budget" if budget else "")
            + ". To send the best matches, could you let me know if you're after a ready unit or off-plan — "
              "and is it to live in or to invest? I'll follow up with a shortlist and recent comparables.")


# ---- the real LLM drafter -------------------------------------------
def make_llm_drafter(provider="openai", api_key=None, model=None, base_url=None,
                     fallback=None, timeout=30):
    """Return a drafter backed by a real LLM. On any failure it falls back to the
    template drafter so the agent never breaks. provider='mock' runs offline."""
    import urllib.request
    fb = fallback or template_drafter

    def drafter(lead, config):
        global LAST_LLM_ERROR
        system = build_system_prompt(config)
        user = "Lead: " + json.dumps(lead)
        if provider == "mock":
            return _mock_answer(lead, config)
        req = build_request(provider, system, user, api_key, model, base_url)
        try:
            r = urllib.request.Request(req["url"], data=json.dumps(req["body"]).encode(),
                                       headers=req["headers"], method="POST")
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return parse_response(provider, data) or fb(lead, config)
        except Exception as ex:
            LAST_LLM_ERROR = repr(ex)
            return fb(lead, config)

    return drafter


# ---- environment-driven selection -----------------------------------
def resolve_drafter(config):
    provider = (os.getenv("LLM_PROVIDER") or "").lower()
    if provider == "mock":
        return make_llm_drafter(provider="mock")
    key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if provider in ("openai", "anthropic", "openai-compatible") and key:
        prov = "anthropic" if provider == "anthropic" else "openai"
        return make_llm_drafter(prov, api_key=key, model=os.getenv("LLM_MODEL"),
                                base_url=os.getenv("LLM_BASE_URL"))
    return template_drafter


def drafter_mode():
    """Human-readable description of what resolve_drafter will use."""
    provider = (os.getenv("LLM_PROVIDER") or "").lower()
    if provider == "mock":
        return "mock LLM (offline — proves the wiring, no network)"
    key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if provider in ("openai", "anthropic", "openai-compatible") and key:
        return f"REAL LLM · {provider} · {os.getenv('LLM_MODEL') or 'default model'}"
    return "offline template (set LLM_PROVIDER + OPENAI_API_KEY to use a real LLM)"
