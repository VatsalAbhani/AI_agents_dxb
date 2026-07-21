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
