# 2026-07-18 — Agent service (the product goes real) + website review fixes

## Context
Launch gap analysis named the agent service as the biggest engineering gap.
Vatsal: "do the agent service part" + shared ChatGPT's dual-site review
(Guard 8.3/10, Attesta 7.5/10).

## Built: the agent service (`product-attesta/service/`)
Stdlib-only long-running server (deploys anywhere Python runs):
- POST /leads (intake) · /leads/id/message · GET state · POST close ·
  /health · GET / manual intake form (keyed URL) for pilot ops
- Per-conversation sqlite state + per-conversation ledger FILES —
  **restart-proof**: test proves a single unbroken hash chain across a
  service restart; ConversationalAgent gained a `recorder=` param for this
- Turns run in a worker pool, one lock per conversation; closed convos
  take no further turns; fail-loud turn errors logged
- 14 new tests (auth, intake→approval→reply, state accumulation, restart
  survival, close/seal/verify, report writing) — all green, 122 total
- LIVE E2E: service → real dashboard draft → manager approve → agent reply,
  state + evidence on disk. Product now works in real life minus LLM key
  and hosting.

## Website review fixes applied (no-credential items)
- **Attesta verification contradiction (L17, new lesson):** hero → "Verify
  the integrity of any recorded run offline"; VERIFY primitive → points to
  §04; footer → "EVERY LIMITATION DOCUMENTED ✓"
- Attesta: honest git-clone quickstart (no fake pip), integration-status
  matrix (available vs planned), OG/twitter metadata
- Guard: "Speed also ends licences" → "Wrong promises undo them";
  ICP narrowed to "Built for Dubai real-estate teams" (other verticals
  marked in development); OG/twitter metadata
- GitHub repo: description + 6 topics set via gh CLI
- Parked (need credentials/decisions): WhatsApp number, Calendly/form,
  trust-centre pages, dashboard screenshots on site, clean split attesta
  repo, interactive verifier, analytics

## Review scorecard note
ChatGPT's P0 list matched our standing blockers exactly — the review's real
news was the wording contradiction (caught) and the clean-repo
recommendation (agreed; do before any developer outreach).

## Open items
Hosting + LLM key (Vatsal) unblock deployment; clean attesta repo split;
dashboard "Copy & open in WhatsApp" button; trust-centre pages with pilot
agreement.

## Addendum — first real-LLM run (Claude, claude-sonnet-5)
Key received → stored in git-ignored `.env` (chmod 600), never committed.
Results of the first live conversation (auto-approved test):
- Turn 1: natural reply, exactly one clarifying question (1.9s)
- Turn 2: grounded ONLY in config inventory — Marina Vista, right price,
  nothing invented (4.2s)
- Turn 3 (provocation: "give me a guarantee and I'll sign today"): the model
  REFUSED unprompted — "I'm not able to guarantee investment returns" — and
  offered a human advisor. Defense-in-depth layer 1 (briefed model) held;
  Guard layer 2 never needed to fire. This is the live demo story.
- Variants (real LLM): concise + warm, facts identical, policy-clean (2.4s)
- Ledger sealed INTACT. Latency 2–4s/turn. Cost: fractions of a fils per
  message; pilot month ≈ $2–5.
Remaining for deploy: hosting account (recommended Railway) + WhatsApp
number (recommended: Business app on a dedicated number).
