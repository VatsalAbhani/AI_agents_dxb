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
import re

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


# ---- multi-turn conversation (used by agent_template.conversation) ---
def template_converse(ctx, config):
    """Deterministic multi-turn drafter. Acts on the qualify decision: ask the
    next missing question, share matched inventory (never invents listings), or
    hand the lead to a human. Offline, compliant by construction."""
    name = (ctx.get("lead") or {}).get("name", "there")
    action = ctx.get("action") or {"type": "ask", "slot": "budget"}
    matches = ctx.get("matches") or []
    first = not any(h.get("role") == "agent" for h in ctx.get("history") or [])
    greet = f"Hi {name} — " if first else ""

    if action["type"] == "escalate":
        return (greet + f"you clearly know what you're looking for, so I'm connecting you with our senior "
                f"consultant at {config.company}, who handles these personally. They'll reach out shortly — "
                "is there anything specific you'd like them to prepare?")

    if action["type"] == "share_options" and matches:
        lines = [f"• {u.get('name')} — {u.get('bedrooms')}BR in {u.get('area')}, AED {u.get('price', 0):,.0f}"
                 + (f" ({u['type']})" if u.get("type") else "")
                 for u in matches[:3]]
        return (greet + "based on what you've shared, these current listings fit:\n" + "\n".join(lines)
                + "\nWould you like more detail or a viewing on any of these?")

    questions = {
        "budget": "what budget range are you considering?",
        "area": "which area of Dubai do you prefer?",
        "timeline": "when are you hoping to move ahead — the next few months, or later?",
        "purpose": "is this to live in yourself, or as an investment?",
    }
    q = questions.get(action.get("slot"), "could you tell me a little more about what you're looking for?")
    return greet + "happy to help — " + q


def build_converse_system_prompt(config):
    """Same guardrails as the single-shot prompt, plus multi-turn grounding rules."""
    return (build_system_prompt(config)
            + "\nYou are mid-conversation. You receive the chat history, what is known about the lead "
              "(slots), matching listings from OUR inventory, and a suggested next step (action). "
              "Only ever mention listings from the provided matches — never invent properties, prices, or "
              "availability. Follow the suggested action: 'ask' = ask that one question, 'share_options' = "
              "present the matches, 'escalate' = warmly hand over to a human colleague. Reply with the "
              "message text only.")


def make_llm_converser(provider="openai", api_key=None, model=None, base_url=None,
                       fallback=None, timeout=30):
    """Multi-turn counterpart of make_llm_drafter: same plumbing and fallback
    behaviour, but briefed with the conversation state. provider='mock' runs
    offline through the LLM code path."""
    import urllib.request
    fb = fallback or template_converse

    def converser(ctx, config):
        global LAST_LLM_ERROR
        if provider == "mock":
            return template_converse(ctx, config)
        state = {"lead": ctx.get("lead"), "slots": ctx.get("slots"),
                 "history": (ctx.get("history") or [])[-8:],
                 "matches": ctx.get("matches"), "action": ctx.get("action")}
        req = build_request(provider, build_converse_system_prompt(config),
                            "Conversation state: " + json.dumps(state, default=str),
                            api_key, model, base_url)
        try:
            r = urllib.request.Request(req["url"], data=json.dumps(req["body"]).encode(),
                                       headers=req["headers"], method="POST")
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return parse_response(provider, data) or fb(ctx, config)
        except Exception as ex:
            LAST_LLM_ERROR = repr(ex)
            return fb(ctx, config)

    return converser


def resolve_converser(config):
    provider = (os.getenv("LLM_PROVIDER") or "").lower()
    if provider == "mock":
        return make_llm_converser(provider="mock")
    key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if provider in ("openai", "anthropic", "openai-compatible") and key:
        prov = "anthropic" if provider == "anthropic" else "openai"
        return make_llm_converser(prov, api_key=key, model=os.getenv("LLM_MODEL"),
                                  base_url=os.getenv("LLM_BASE_URL"))
    return template_converse


# ---- on-demand draft alternatives (used by the approval dashboard) ---
def _fallback_variants(draft):
    """Deterministic tone variants: (1) more concise, (2) warmer. Used offline
    and as the safety net when the LLM call fails."""
    draft = (draft or "").strip()
    out = []
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", draft) if p.strip()]
    if len(parts) > 2:
        out.append(" ".join([parts[0], parts[-1]]))
    elif len(parts) == 2:
        out.append(parts[-1])
    else:
        trimmed = re.sub(r"^(hi|hello|dear)[^\u2014:,–-]*[\u2014:,–-]\s*", "", draft, flags=re.I).strip()
        out.append(trimmed)
    out.append(draft + " No pressure at all — happy to help however suits you best.")
    return out


def _llm_variant_gen(provider, api_key, model, base_url, timeout=30):
    import urllib.request

    def gen(draft, context):
        global LAST_LLM_ERROR
        system = ("You rewrite an already-drafted customer message in alternative phrasings. "
                  "Produce exactly 2 alternatives: (1) more concise, (2) warmer and more personal. "
                  "Keep every fact, price and commitment identical. Never add promises, guarantees, "
                  "discounts or availability claims. Reply with ONLY a JSON array of 2 strings.")
        req = build_request(provider, system, "Draft: " + json.dumps(draft), api_key, model, base_url)
        try:
            r = urllib.request.Request(req["url"], data=json.dumps(req["body"]).encode(),
                                       headers=req["headers"], method="POST")
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            text = parse_response(provider, data)
            arr = json.loads(text[text.index("["):text.rindex("]") + 1])
            return [str(x) for x in arr][:2]
        except Exception as ex:
            LAST_LLM_ERROR = repr(ex)
            return _fallback_variants(draft)

    return gen


def make_variants(config, gen=None):
    """Build callable(draft, context) -> up to 2 alternative phrasings for the
    approval dashboard's "Alternatives" button. Uses the LLM when configured
    (same env vars as the drafter), deterministic tone variants otherwise.
    Every variant passes the SAME policy gate as the original draft — a
    blocked variant is silently dropped, never offered to the manager."""
    from .config import build_policies
    from attesta.policy import evaluate
    pols = build_policies(config)

    if gen is None:
        provider = (os.getenv("LLM_PROVIDER") or "").lower()
        key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if provider in ("openai", "anthropic", "openai-compatible") and key:
            prov = "anthropic" if provider == "anthropic" else "openai"
            gen = _llm_variant_gen(prov, key, os.getenv("LLM_MODEL"), os.getenv("LLM_BASE_URL"))
        else:
            gen = lambda draft, ctx: _fallback_variants(draft)

    def variants(draft, context=None):
        try:
            vs = gen(draft, context) or []
        except Exception:
            vs = _fallback_variants(draft)
        clean = []
        for v in vs:
            v = (v or "").strip()
            if v and v != draft and v not in clean and evaluate(v, pols)["decision"] != "block":
                clean.append(v)
        return clean[:2]

    return variants
