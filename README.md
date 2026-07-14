# AI Agents DXB

Everything from building an AI startup in Dubai — from "what should I build?" all the way to a working,
tested product. This repo holds the **product**, the **research/strategy** behind it, and the earlier
**prototypes** we built and moved on from.

> Founder: **Vatsal** · acting cofounder/CTO: **Fable (Claude)** · base: **Dubai, UAE**

---

## 🧭 The short story

We explored several directions (a Dubai AML‑compliance tool, a Dubai real‑estate platform), pressure‑tested
how crowded each market was, then deliberately hunted for a *less‑crowded, higher‑ceiling* space. That led —
through a scored shortlist — to **AI‑agent infrastructure**, and to the product now in this repo:

**Attesta** — a *verifiable, tamper‑evident flight recorder for AI agents* (the long‑term, billion‑dollar
infrastructure), with **Leadcode Guard** on top — the sellable business product that lets companies deploy
AI agents *safely* (policy checks + human approval + an audit trail you can prove). The **Lead Follow‑up
Agent** is the first productized, per‑client unit you can sell to a Dubai brokerage today.

Business model: sell the safe agent as a service now (through the existing marketing company) → productize
what repeats → extract Attesta Core as the platform other companies and agencies buy. Revenue now, without
abandoning the billion‑dollar core.

---

## 📁 What's in here

```
AI_agents_dxb/
├── product-attesta/     ⭐ THE PRODUCT — Attesta Core + Leadcode Guard + Lead Follow-up Agent
│   ├── attesta/           ledger · recorder · replay · verifier · cli   (the $1B engine)
│   │                      policy · gateway · redact · report            (Leadcode Guard layer)
│   ├── agent_template/    the sellable per-client agent (real LLM wired in, env-driven)
│   ├── examples/          demo_agent.py · leadcode_guard_demo.py · .html · realestate_pilot.py
│   ├── tests/             55 checks, no pytest needed
│   └── README.md          ← full product docs + how to run
│
├── research/            📚 the thinking (strategy + deep research)
│   ├── Attesta_Flight_Recorder_DeepDive.docx     the chosen idea, deep-dived
│   ├── Idea_Scorecard.md                         8 infra ideas scored & ranked
│   ├── Less_Contested_AI_Shortlist.md            how we found the space
│   ├── More_Infra_Ideas.md                       the infra idea batch
│   ├── Competitive_Landscape_How_Crowded.md      honest market-crowding scan
│   ├── Dubai_Gateway_Venture_Research.docx        the real-estate direction (explored)
│   ├── Amana_Founding_Plan.docx                   the compliance direction (explored)
│   └── CONTEXT_HANDOFF.md                         early research handoff notes
│
└── prototypes/          🧪 earlier builds we moved on from (kept for reference)
    ├── Amana_App/          AML/goAML compliance tool (STR/REAR/DPMSR + UBO tracer)
    └── Dubai_Gateway_App/  real-estate lead funnel: landing + ROI/visa tools + CPQL dashboard
```

---

## 🚀 Run the product (30 seconds, no install)

```bash
cd product-attesta

python examples/demo_agent.py            # the pure Attesta core: record → verify → replay → catch tampering
python examples/realestate_pilot.py      # the sellable pilot: AI drafts → policy → approval → audit report
python tests/test_core.py                # 14 checks   (run the others too: gateway / agent_template / llm)
```

Use a **real LLM** — no code change, just environment variables:

```bash
export LLM_PROVIDER=openai  OPENAI_API_KEY=sk-...  LLM_MODEL=gpt-4o-mini
python examples/realestate_pilot.py
# LLM_PROVIDER=mock runs the real LLM code path offline (no key) to prove the wiring
```

Open `product-attesta/examples/leadcode_guard_demo.html` in a browser for a **clickable demo** to show a prospect.

Full details: **[product-attesta/README.md](product-attesta/README.md)**.

---

## ✅ Status

- Working **v0.2**, pure‑Python stdlib core, **55 automated tests passing**.
- Honest edges (documented in the product README): HMAC seal stands in for KMS/Sigstore; framework
  adapters + OpenTelemetry export are next; policy engine is keyword‑based for now.

## ▶️ Suggested next builds

1. A real **framework adapter** (LangGraph / OpenAI Agents SDK) so it captures a real agent automatically.
2. **WhatsApp Business API** send, to turn the pilot into a live deployment.
3. A thin **hosted approval dashboard** so a manager approves from their phone.

*This repo is the durable backup of the whole journey. Built in Cowork mode with Claude.*
