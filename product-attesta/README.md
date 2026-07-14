# Attesta — the flight recorder for AI agents

**Verifiable, tamper-evident action ledger + deterministic replay for AI agents.**

> **Two layers, one core.**
> **Attesta Core** is the verifiable-evidence *infrastructure* (ledger + replay + verifier) — the long-term, billion-dollar path.
> **Leadcode Guard** is the first *business application* built on top of it: a gateway that policy-checks and human-approves what AI agents send **before** they act, and proves it after. You sell the outcome (safety, approval, proof); the Core is the engine underneath.

Agents are non-deterministic software that take real actions — calling tools, moving data, spending
money. When one misbehaves you hit two walls: *you can't reproduce the failure*, and *you can't prove
what happened*. Observability tools store **mutable** traces for debugging; they don't give you an
**independently verifiable** record or a faithful **replay**. Attesta does both — and the Gateway adds
control *before* the action, not just logging after.

```
record  →  verify (offline)  →  replay  →  catch tampering  →  catch code drift
```

> **v0 / zero dependencies.** Pure Python stdlib — runs anywhere, no install needed. This is the
> open-source core; the hosted cloud (retention, anchoring, compliance exports) sits on top.

---

## See it in 30 seconds

```bash
python examples/demo_agent.py
```

```
[1] RECORDED a run · 4 entries · merkle=ebed03cdd637...
[2] VERIFY offline · chain_ok=True root_matches_seal=True signature_valid=True → INTACT ✓
[3] REPLAY the exact run · reproduced=True → REPRODUCED ✓ (signed)
[4a] Someone forges the recorded temperature → TAMPER DETECTED ✓ (entry #2 hash mismatch)
[4b] The agent code changes → DIVERGENCE [control_flow] / [input_changed] / [extra_call]
```

### The business demo (Leadcode Guard)

```bash
python examples/leadcode_guard_demo.py
```

```
[1] Lead received: 2BR Downtown Dubai, budget AED 2.5M (from Meta Ads)
[2] AI drafted reply #1 → policy: needs approval → manager approved → SENT
[3] AI draft #2 "...guaranteed to appreciate 20%..." → policy: BLOCKED → manager rewrote → SENT
[4] Attesta integrity check → INTACT ✓ (13 actions)
[5] Audit report → leadcode_audit_report.md
[6] Privacy: raw phone stored? NO ✓ (redacted)
[7] Someone edits a sent message → TAMPER DETECTED ✓
```

Run the tests (no dependencies):

```bash
python tests/test_core.py        # 14 checks — the core
python tests/test_gateway.py     # 14 checks — safe-replay, redaction, policy, gateway
```

---

## Instrument your agent (the whole API)

Route your agent's non-deterministic boundaries through a `Recorder`. That's it.

```python
from attesta import Recorder, replay, verify
from attesta.ledger import Ledger

def my_agent(rec, goal, city):
    ts      = rec.now()                                  # time is recorded
    plan    = rec.llm("planner", call_llm, f"goal={goal}")   # LLM call recorded
    weather = rec.tool("weather", weather_api, city)         # tool call recorded
    return rec.llm("writer", call_llm, f"{plan} {weather}")

# RECORD
rec = Recorder("record")
answer = my_agent(rec, "Should I go outside?", "Dubai")
rec.ledger.seal(key="...")          # prod: KMS / Sigstore
rec.ledger.save("run.jsonl")

# VERIFY (offline, no server, no trust)
print(verify("run.jsonl", key="..."))    # {'intact': True, ...}

# REPLAY (reproduce, or get a signed divergence report)
report = replay(my_agent, Ledger.load("run.jsonl"), "Should I go outside?", "Dubai")
print(report["reproduced"], report["divergences"])
```

CLI:

```bash
python -m attesta.cli show   run.jsonl
python -m attesta.cli verify run.jsonl --key ...
```

---

## How it works

**1. Tamper-evident ledger** (`ledger.py`) — every action is an append-only, **hash-chained** entry
(each commits to the previous). At seal time we compute a **Merkle root** and sign it. Any later edit
breaks a hash, a chain link, or the signature.

**2. Offline verifier** (`verifier.py`) — recomputes the whole chain + Merkle root and checks the
signature. Anyone can verify a run's integrity **without trusting Attesta's servers** — that's the
point.

**3. Record/replay engine** (`recorder.py`, `replay.py`) — records every non-deterministic input
(LLM outputs, tool responses, time, randomness). On replay it serves those recorded inputs back, so
the run reproduces — and if the agent tries a *different* call, order, or input, that **divergence** is
detected and the verdict is signed. **Replay never makes live calls** (side-effect-safe), and an
optional **redactor** scrubs PII from what's stored while integrity hashes stay over the originals.

**4. Gateway + policy (Leadcode Guard layer)** (`gateway.py`, `policy.py`, `report.py`) — sits
*between the agent and its tools*: it runs a policy check and (if needed) human approval **before** an
action executes, records every decision to the Core ledger, and exports a client-ready **audit report**.
This is what turns the infrastructure into a product a business owner buys.

### An honest note on "deterministic replay"

LLMs are not bit-for-bit reproducible (seed exposure varies by provider; hardware nondeterminism).
Attesta doesn't pretend otherwise. It **records inputs, re-runs against them, and cryptographically
reports reproduced-vs-diverged.** "Verifiable divergence detection" is more useful — and more honest —
than a reproduction promise nobody can keep.

---

## Why this vs. your tracing tool

|  | Mutable tracing (Datadog / LangSmith) | Replay tools (AgentOps / Temporal) | **Attesta** |
|---|---|---|---|
| Cryptographically tamper-evident | ✗ | ✗ | **✓** |
| Independently verifiable offline | ✗ | ✗ | **✓** |
| Deterministic replay / divergence | ✗ | partial | **✓ (honest)** |
| Cross-framework + MCP, neutral | varies | varies | **✓** |
| Developer-first (not a compliance sale) | ✓ | ✓ | **✓** |

The tools that do tamper-evidence today sell to compliance officers; the tools developers use don't do
tamper-evidence. Attesta is the **developer-first** product that does both.

---

## Roadmap

- **Now (v0.2):** hash-chained ledger, Merkle seal, offline verifier, **side-effect-safe** record/replay + divergence, **PII redaction hook**, **policy engine + approval gateway**, **audit report**, CLI.
- **Next:** first-class adapters (OpenAI Agents SDK, Claude Agent SDK, LangGraph, CrewAI) + an **MCP proxy**; OpenTelemetry-GenAI span emission.
- **Cloud:** hosted tamper-proof retention, **Sigstore/RFC-3161 anchoring**, asymmetric signing (KMS), team dashboard, replay-as-a-service.
- **Evidence:** auditor-verifiable export packs (EU AI Act Art. 12 / DORA / SOC 2 / HIPAA).
- **Destination:** signed **agent action-receipts** → the trust & authorization rail for agent payments.

## Deploy the agent for a client (the product template)

The **Lead Follow-up Agent** turns "we build agents" into a repeatable unit. To onboard a new client you
write a config — not code — and the same agent reads leads, drafts replies, runs them through Guard, and
produces the audit report.

```python
from agent_template import LeadFollowupAgent, realestate_config

agent = LeadFollowupAgent(realestate_config("ABC Real Estate"),
                          approver=manager_approves, remediator=manager_rewrites)
for lead in leads:
    agent.process(lead)                 # AI drafts → policy → approval → send, all recorded
out = agent.finalize(key="...", path="run.jsonl")   # verified ledger + audit report
```

Try it: `python examples/realestate_pilot.py` (3 leads sent, 1 salesy draft blocked+rewritten, INTACT
audit report).

**Use a real LLM** — no code change, just environment variables (the drafter auto-resolves):

```bash
export LLM_PROVIDER=openai         # or: anthropic | openai-compatible | mock
export OPENAI_API_KEY=sk-...       # or ANTHROPIC_API_KEY
export LLM_MODEL=gpt-4o-mini       # optional
python examples/realestate_pilot.py
# LLM_PROVIDER=mock runs the real LLM code path offline (no key, no network) to prove the wiring
```

The model is briefed with the **same guardrails Guard enforces** (defense in depth), the AI draft is
recorded into the Attesta ledger, and if the API call ever fails the agent **falls back to the template
drafter** instead of breaking. To actually send, swap the stub sender for the WhatsApp Business API.

## Project layout

```
attesta/          ledger.py · recorder.py · replay.py · verifier.py · cli.py   ← Attesta Core (the $1B engine)
                  policy.py · gateway.py · redact.py · report.py               ← Leadcode Guard layer
agent_template/   agent.py · config.py · drafter.py (real LLM + mock + fallback)   ← the sellable product template
examples/         demo_agent.py · leadcode_guard_demo.py · leadcode_guard_demo.html · realestate_pilot.py
tests/            test_core.py (14) · test_gateway.py (14) · test_agent_template.py (11) · test_llm.py (16)   # 55 checks, no pytest
```

## Status & license

Working v0.2, honest about its edges. Replay is now side-effect-safe and PII is redacted from storage
while integrity holds. Still not production-hardened: HMAC seal stands in for KMS/asymmetric + Sigstore
anchoring; no framework adapters or OpenTelemetry export yet; policy engine is keyword-based (real
product uses stronger classification). Apache-2.0.
