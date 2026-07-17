"""
Tests for the real-LLM wiring (no network needed):  python tests/test_llm.py

Proves the integration is correct — request built right, guardrails injected,
responses parsed, mock provider works end-to-end, and a failed real call falls
back gracefully instead of breaking the agent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.config import realestate_config          # noqa: E402
from agent_template.drafter import (                          # noqa: E402
    build_system_prompt, build_request, parse_response,
    make_llm_drafter, resolve_drafter, template_drafter,
)
from agent_template.agent import LeadFollowupAgent            # noqa: E402

P, F = {"n": 0}, {"n": 0}


def ok(name, cond):
    (P if cond else F)["n"] += 1
    print(("  ✓ " if cond else "  ✗ FAIL: ") + name)


cfg = realestate_config("ABC Real Estate")
LEAD = {"name": "Rahul", "area": "Downtown Dubai", "budget": "AED 2.5M"}

print("\n== the model is briefed with the SAME guardrails Guard enforces ==")
sys_prompt = build_system_prompt(cfg)
ok("prompt forbids guaranteed returns", "guaranteed" in sys_prompt.lower() and "return" in sys_prompt.lower())
ok("prompt names the company + tone", "ABC Real Estate" in sys_prompt and cfg.tone.split(",")[0] in sys_prompt)

print("\n== OpenAI request is built correctly ==")
ro = build_request("openai", sys_prompt, "Lead: {}", "sk-test", "gpt-4o-mini", None)
ok("openai url correct", ro["url"] == "https://api.openai.com/v1/chat/completions")
ok("bearer auth header", ro["headers"]["authorization"] == "Bearer sk-test")
ok("system + user messages present", ro["body"]["messages"][0]["role"] == "system" and ro["body"]["messages"][1]["role"] == "user")

print("\n== Anthropic request is built correctly ==")
ra = build_request("anthropic", sys_prompt, "Lead: {}", "k", "claude-sonnet-5", None)
ok("anthropic url correct", ra["url"] == "https://api.anthropic.com/v1/messages")
ok("x-api-key + version headers", ra["headers"]["x-api-key"] == "k" and "anthropic-version" in ra["headers"])
ok("system passed as top-level field", ra["body"]["system"] == sys_prompt)

print("\n== responses parse for both providers ==")
ok("openai parse", parse_response("openai", {"choices": [{"message": {"content": "hello"}}]}) == "hello")
ok("anthropic parse", parse_response("anthropic", {"content": [{"text": "hi"}]}) == "hi")

print("\n== mock provider produces a real draft end-to-end (offline) ==")
mock = make_llm_drafter(provider="mock")
draft = mock(LEAD, cfg)
ok("mock draft is non-trivial + on-topic", len(draft) > 40 and "Downtown Dubai" in draft)
agent = LeadFollowupAgent(cfg, drafter=mock,
                          approver=lambda d, c: {"decision": "approve", "final": d, "by": "Mgr"})
res = agent.process(LEAD)
ok("agent sends the LLM-drafted message", res["status"] == "sent")
ok("the LLM draft is recorded in the Attesta ledger", any(e["type"] == "llm" and e["name"] == "draft" for e in agent.rec.ledger.entries))

print("\n== a failed real call falls back gracefully (no crash) ==")
broken = make_llm_drafter(provider="openai", api_key="x", base_url="http://127.0.0.1:9")  # unreachable
out = broken(LEAD, cfg)
ok("fell back to template text instead of crashing", out == template_drafter(LEAD, cfg))

print("\n== on-demand variants (Alternatives button) ==")
from agent_template.drafter import make_variants, _fallback_variants  # noqa: E402
long_draft = ("Hi Rahul — happy to help. We have two strong options in Dubai Marina right now. "
              "Both are ready units with good layouts. Shall I set up a viewing this week?")
fv = _fallback_variants(long_draft)
ok("fallback returns 2 variants", len(fv) == 2)
ok("concise variant is shorter", len(fv[0]) < len(long_draft))
ok("variants differ from the draft", all(v != long_draft for v in fv))

vgen = make_variants(realestate_config("ABC"))
vs = vgen(long_draft, {})
ok("make_variants returns ≤2 clean variants", 0 < len(vs) <= 2 and all(v != long_draft for v in vs))

bad_gen = lambda d, c: ["A perfectly fine alternative phrasing.",
                        "We guarantee 20% returns if you sign today!"]
filtered = make_variants(realestate_config("ABC"), gen=bad_gen)(long_draft, {})
ok("policy-violating variant is dropped", len(filtered) == 1 and "guarantee" not in filtered[0])

print("\n== env-driven resolver ==")
os.environ.pop("LLM_PROVIDER", None); os.environ.pop("OPENAI_API_KEY", None)
ok("no env -> offline template", resolve_drafter(cfg) is template_drafter)
os.environ["LLM_PROVIDER"] = "mock"
ok("LLM_PROVIDER=mock -> LLM code path", resolve_drafter(cfg) is not template_drafter)
os.environ.pop("LLM_PROVIDER", None)

print(f"\nRESULT: {P['n']} passed, {F['n']} failed")
sys.exit(1 if F["n"] else 0)
