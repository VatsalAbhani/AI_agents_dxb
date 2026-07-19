# 2026-07-17 — Community signals → four features + alternatives

## Context
Vatsal brought a ChatGPT research doc on r/CommercialRealEstate. My critique:
signal real (triple-confirmed with KT + JLL: AI for the first mile, humans for
judgment; "Approval is not friction — it's the feature"), but the doc was a
6-month agenda dressed as a 30-day plan (L15). Adopted 4 items now, parked the
rest (source-backed claims → build inside pilot #1 against real inventory).

## Built (commit 25ff7ff)
1. **High-intent handoff** — `handoff.requested` ledger event on first
   escalation; intent forwarded to dashboard; priority queue-jump + flagged
   card; median handoff time = headline pilot KPI (stats strip + /api/metrics).
2. **Relationship-sensitivity policy** — returning/referral/personal =
   draft-only; `routed_to_advisor` delivery; badge + explainer in UI.
3. **Edit/reject reasons** — dialogs → DB → gateway approval event in ledger;
   shown in Activity.
4. **PILOT-METRICS.md** — KPI definitions/sources/targets, weekly report
   template, ground rules, and the thesis test: renewal willingness WITH vs
   WITHOUT Guard (ask verbatim in every debrief).

## Also built
- `examples/live_chat.py` (commit e7d8131) — interactive lead in terminal +
  dashboard approvals; the pitch-meeting demo. (dashboard_pilot.py confusion:
  it's a 2-message scripted demo that ends by design.)
- **Alternatives on demand** (commit 487929e) — Vatsal proposed 3 drafts per
  approval; pushed back on default-3 (L10), built on-demand instead:
  "Alternatives" button → agent generates 2 policy-filtered variants
  (`drafter.make_variants`, LLM or offline) → tap-to-send → chosen index in
  verdict + ledger; ALT #n badge; demo seeds Sara with ready variants.
  Watch pilot %-edited vs %-alt-chosen to decide if proactive options earn in.

## Verification
108 Python tests; UI click-through; two full agent↔dashboard E2Es (variants
loop: request → generate → pick → sent text = chosen variant, sealed INTACT).

## Standing blockers (unchanged — the real bottleneck)
WhatsApp number · Calendly · email confirmation · AI Seal application ·
**first outreach message**.
