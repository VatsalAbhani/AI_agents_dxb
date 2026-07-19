# 2026-07-15 — Approval dashboard (the last pilot gap)

## Context
Roadmap #2 from the brief: a screen where a client manager approves drafts
from their phone. Vatsal green-lit; tools vetted first (ui-ux-pro-max skill =
benign, applied its UX checklist; 21st.dev = shadcn substrate).

## What we did
1. **Scaffold:** Next.js 16.2 + Tailwind v4 + shadcn/ui (radix base) +
   better-sqlite3, port 3005, in `dashboard/`. (CLI flag drift → L11.)
2. **API:** `POST /api/drafts` (agent submits, x-api-key), `GET /api/drafts/:id`
   (agent polls), `POST /api/drafts/:id/decide` (manager), `POST /api/demo`
   (seeder). SQLite singleton with WAL.
3. **UI:** mobile-first approvals queue (44px+ targets, AA contrast — orange
   primary with ink text), Pending/Activity tabs, edit dialog, sonner toasts,
   4s polling. Brand: mono wordmark header, product-boring by design.
4. **Python bridge:** `agent_template/approvals.py` `remote_approver()` —
   zero-dep, Gateway contract, **fails closed** on timeout/unreachable/401.
   `examples/dashboard_pilot.py` (2-message scripted demo).
5. **Verified:** browser click-through of all flows (fixed toast-blocking-tabs
   and duplicate channel chip); agent E2E — browser approval unblocked the
   polling agent → SENT; undecided draft timed out → fail-closed reject (L8);
   ledgers INTACT; 87 Python tests.

## Decisions & rejected alternatives
- Poll-based approver over websockets/queues (pilot-grade, zero-dep).
- Fail-closed timeout = reject (rejected: fail-open or infinite wait).
- No login for pilot #1 (private URL per client); documented upgrade path.

## Outcome
Commit: `88f2dbf`. Stack complete: agent → Guard → phone → ledger → report.

## Open items
WhatsApp ping to manager when a draft waits; per-client auth before multi-tenant.
