# Leadcode Guard — Pilot Metrics Sheet

The numbers we commit to measuring in every 14-day pilot, what each one means,
where it comes from, and the weekly report template built from them. This sheet
is shown to the client **before** the pilot starts — "here is exactly what we
will measure" — and the same table becomes the end-of-pilot report.

Two sources of truth:
- **Dashboard** — live at `/api/metrics` (approval-side numbers).
- **Ledger** — the sealed Attesta run files (agent-side numbers: blocks,
  remediations, handoff events), summarised by the audit report.

---

## 1 · Operational value (does it make the team faster?)

| Metric | Definition | Source | Pilot target |
| --- | --- | --- | --- |
| Median first-response time | Lead message → approved reply sent | Ledger (`lead.message` → `whatsapp.sent` ts) | < 5 min in working hours |
| Response coverage | % of enquiries receiving a reply | Ledger vs. lead-source count | > 95% (vs. baseline measured in week 0) |
| Median decision time | Draft submitted → manager decision | Dashboard `median_decision_ms` | < 10 min in working hours |
| Drafting time saved | Drafts produced × est. manual minutes per reply | Dashboard `decided` × client's estimate | reported, not promised |

## 2 · High-intent handoff (does it accelerate deals?)

| Metric | Definition | Source | Pilot target |
| --- | --- | --- | --- |
| **Median handoff time** | High-intent signal detected → human takes over | Dashboard `median_handoff_ms` (agent `handoff.requested` in ledger corroborates) | **< 15 min** — the headline pilot number |
| High-intent leads surfaced | Escalations flagged by the agent | Dashboard `high_intent_total` | count reported weekly |
| Appointments/viewings booked | Booked from AI-assisted conversations | Client CRM / manual tally | count reported weekly |

## 3 · Human-control value (is the approval loop healthy?)

| Metric | Definition | Source | Healthy range |
| --- | --- | --- | --- |
| % approved unchanged | Drafts sent exactly as the AI wrote them | Dashboard `pct_approved_unchanged` | 60–90% (lower = drafter needs tuning) |
| % edited | Approved with manager changes | Dashboard `pct_edited` | 10–30% |
| % rejected | Nothing sent | Dashboard `pct_rejected` | < 10% |
| Edit/reject reasons | Free-text reasons captured per decision | Dashboard `reason` column | reviewed weekly → drafter/policy tuning |
| Relationship leads protected | Returning/referral leads routed to human sender | Ledger `routed_to_advisor` tool events | 100% (hard rule) |

## 4 · Guard-specific value (what did the controls catch?)

| Metric | Definition | Source | Notes |
| --- | --- | --- | --- |
| Risky claims blocked | Drafts stopped by policy before any human saw a send button | Ledger `policy.check BLOCK` events | each one is a story for the weekly report |
| Compliant rewrites | Blocked → remediated → approved | Ledger `remediation.redraft` events | shows the system recovers, not just refuses |
| Messages held awaiting approval | Nothing ever auto-sent | Ledger (no `sent` without prior `approval`) | the core guarantee |
| Ledger integrity | Sealed run verifies INTACT | `attesta verify` on the run file | must be 100% |

## 5 · Commercial value (should anyone renew?)

| Metric | Definition | Source |
| --- | --- | --- |
| Qualified conversations | Leads reaching budget/timeline/area qualification | Ledger `qualify` events |
| Appointments booked | From AI-assisted conversations | Client CRM |
| Cost per re-engaged lead | Pilot fee ÷ leads engaged | Simple division, reported honestly |
| **Renewal willingness — with vs. without Guard** | Debrief question: *"Would you keep this if it were just the chatbot, without the approval queue and the record?"* | Founder-led debrief |

That last question is the company thesis test. If clients would renew without
the trust layer, we learned we're selling a chatbot. If the approval queue and
the proof pack are the reason they keep it, Attesta is validated with revenue.
Ask it every time, verbatim, and write the answer down.

---

## Weekly pilot report template

```
LEADCODE GUARD · PILOT WEEK N — [Client]
─────────────────────────────────────────
Leads handled:            __   (coverage __%)
Median first response:    __
High-intent handoffs:     __   (median handoff time __)
Appointments booked:      __

Approval loop:  __% unchanged · __% edited · __% rejected
Top edit/reject reasons:  1) __  2) __  3) __

Guard catches:  __ risky drafts blocked · __ compliant rewrites
Relationship leads protected: __/__ routed to human sender

Ledger: __ actions recorded · integrity INTACT ✓
Next week's tuning: __
```

## Ground rules for using these numbers

- **Never promise closed deals.** Promise measurable operational improvement;
  report deal outcomes when they happen.
- **Baseline first.** Capture the client's current first-response time and
  coverage in week 0, or the improvement claim means nothing.
- **Report failures openly.** Missed leads, bad drafts, downtime — they go in
  the weekly report too. Trust is also produced by how we deliver.
- Vendor-style stats ("3.4x more closings") never appear in our reports.
