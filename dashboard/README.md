# Leadcode Guard — Approval Dashboard

The screen a client manager lives in: every AI draft arrives here, and a human
approves, edits, or rejects it **before** anything reaches a customer. Built
mobile-first — managers decide from their phone.

Next.js 16 · Tailwind v4 · shadcn/ui · SQLite (better-sqlite3).

## Run

```bash
npm install
npm run dev          # http://localhost:3005 → /approvals
```

Empty queue? Tap **Load demo data** (or `curl -X POST localhost:3005/api/demo`).

## Wire the agent to it

The Python agent (in `../product-attesta`) plugs in with one line:

```python
from agent_template.approvals import remote_approver

agent = ConversationalAgent(config,
    approver=remote_approver("http://localhost:3005", client="ABC Real Estate"))
```

Full walkthrough: `python ../product-attesta/examples/dashboard_pilot.py` while
the dashboard is running — drafts appear here, your decision unblocks the agent,
everything lands in the Attesta ledger.

## API

| Endpoint | Who | Auth |
| --- | --- | --- |
| `POST /api/drafts` | agent submits a draft | `x-api-key` (env `GUARD_API_KEY`, default `demo-key`) |
| `GET /api/drafts/:id` | agent polls the decision | — |
| `GET /api/drafts?status=` | dashboard lists | — |
| `POST /api/drafts/:id/decide` | manager decides | — |
| `POST /api/demo` | seed sample drafts | — |

The agent client **fails closed**: if the dashboard is unreachable or the
approval times out, the draft is rejected — an unreviewed message is never sent.

## Pilot-grade, deliberately

Single tenant, no login (run it on a private URL per client), SQLite file in
`data/`. Before multi-client production: per-client auth tokens, Postgres,
push notifications (WhatsApp ping to the manager), and hosted deployment.
