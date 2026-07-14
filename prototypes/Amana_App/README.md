# Amana — Compliance Suite (v0.1)

The first working slice of Amana. Three tools for UAE DNFBPs (real-estate brokers, gold dealers,
corporate-service firms, accountants), in one local, no-install app:

1. **goAML Filing Engine** — turns a guided form into a review-ready **STR / REAR / DPMSR** narrative
   **+ goAML-structured XML**, with validation, the AED 55,000 threshold check, and deadlines.
2. **CDD & UBO onboarding** — capture a customer, optionally read their ID with AI, **trace the
   ownership tree to the Ultimate Beneficial Owner (25%+ test)**, and produce a **risk rating** with the
   actions the MLRO must take.
3. **AI assist (optional)** — polish a drafted narrative and extract fields from an ID photo, with
   **privacy-first reversible redaction**. Off by default; the app is fully useful without it.

Everything runs in the browser. **No data leaves the device unless you explicitly turn on a cloud AI
provider** in settings — important for a compliance tool.

---

## Run it

No install, no account, no internet required for the core features:

1. Keep **all files together in one folder** (`index.html` needs `engine.js`, `cdd.js`, `ai.js` beside it).
2. Double-click `index.html` (any modern browser).
3. Use the top nav to switch between **① Filing Engine**, **② CDD & UBO**, and **⚙ AI settings**.
4. Hit **Load sample** in either tool to see it work instantly.

### Try this 60-second demo
- **Filing Engine → Load sample** → a full STR narrative + goAML XML appears. Click **✨ AI polish**
  (works offline as a "tidy"; add a key in AI settings for real AI).
- **CDD & UBO → Load sample** → watch the ownership tree resolve: *Ahmed Ben Salah = 36%* (60% of
  Marina Holdings × 60% of Gulf Trading) and *Sara Ali = 40%* flagged as UBOs; *Lena Cruz = 24%* below
  the line. A risk rating and CDD summary generate. Click **Use subject in Filing Engine →** to carry it over.

---

## Project structure

```
Amana_App/
├─ index.html        The app: three views (Filing / CDD & UBO / AI settings). Vanilla JS, no CDN.
├─ engine.js         Filing engine: report specs, indicator taxonomy, narrative + goAML-XML, validation.
├─ cdd.js            CDD & UBO: recursive ownership tracer (25% test) + transparent risk-rating engine.
├─ ai.js             Optional AI: reversible PII redaction, prompts, offline tidy, provider calls.
├─ README.md         This file
├─ PRODUCT_SPEC.md   The compliance model the code implements
└─ test/
   ├─ sample_run.js    Node: STR/REAR/DPMSR narratives + XML for 3 cases
   ├─ cdd_ai_test.js   Node: 27 unit checks (UBO math, risk, redaction round-trip, prompts, parsers)
   └─ ui_smoke.js      Node + jsdom: loads the real page, runs both flows end-to-end (21 checks)
```

## Architecture

- **Logic is separated from UI.** `engine.js`, `cdd.js`, `ai.js` are pure modules that run in the
  browser *and* in Node (so they're unit-tested). The HTML is a thin driver. When we move to a hosted,
  multi-user product, the UI changes but this logic core largely carries over.
- **Human-in-the-loop by design.** Amana drafts, traces, and rates; a licensed MLRO reviews, approves,
  and files. Amana never submits, and never makes the final UBO/risk call.
- **Privacy-first AI.** The AI layer is optional and off by default. When enabled, reversible redaction
  swaps IDs/emails for opaque tokens before anything is sent to a provider, then restores them locally —
  the provider never sees real identifiers.

## Test it

```bash
cd Amana_App
node test/sample_run.js       # engine: narratives + XML (writes to test/output/)
node test/cdd_ai_test.js      # 27 unit checks (UBO, risk, redaction, prompts)
npm i jsdom && node test/ui_smoke.js   # 21 end-to-end UI checks
xmllint --noout test/output/STR_goaml.xml && echo OK   # optional XML validation
```

---

## Using the optional AI

1. Go to **⚙ AI settings**, pick a provider (Anthropic or OpenAI-compatible), paste an API key (stored
   only on this device), set a model, and keep **redact** on.
2. In the Filing Engine, **✨ AI polish** improves the narrative's clarity without inventing facts.
3. In CDD & UBO, **✨ Extract with AI** reads an uploaded ID/licence photo into the fields.

**Browser/CORS note:** calling public LLM APIs directly from a `file://` page can be blocked by CORS.
Anthropic is called with the browser-access header; some setups still need a small local proxy or
Amana's future backend. The **offline tidy** and everything else always work without a provider.

## Honest scope & disclaimers

- **Decision-support, not the filer.** A licensed MLRO reviews, approves, and files every report and
  confirms every UBO/risk determination.
- **goAML XML is modelled on the schema** and must be reconciled with the UAE FIU's current XSD / import
  template before any live submission. Indicator codes are Amana-internal placeholders mapped per schema version.
- **UBO tracing uses the 25% control test as a guide**, with a senior-managing-official fallback — not legal advice.
- **Thresholds/deadlines** reflect our mid-2026 research; confirm against current Ministry of Economy / FIU guidance.

## Roadmap to v1 (next)

1. **Live screening** — real PEP / sanctions / adverse-media screening with false-positive triage (today
   the app *captures* screening results; next it *performs* them).
2. **Compliance cockpit** — multi-client dashboard, deadline reminders, immutable audit log, one-click inspection pack.
3. **Direct goAML integration** — schema-validated export / API once we have reference customers and access.
4. **In-region AI** — route the optional AI to an enterprise/in-region endpoint (removes the CORS caveat, strengthens PDPL posture).
5. **Productionization** — hosting, auth, encrypted storage, SOC 2 / ISO 27001.

*Amana v0.1 — the first proof that dreaded manual compliance becomes minutes of reviewed, audit-ready output.*
