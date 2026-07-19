# Project Journal — Attesta / Leadcode Guard

Everything we do, why we did it, what happened, and what we learned — one dated
entry per work block. Git records the code; this journal records the reasoning.

**Rules of the journal**
1. Every substantial work block gets an entry (or extends the day's entry).
2. Every mistake becomes a numbered lesson in [LESSONS.md](LESSONS.md) —
   consult it BEFORE starting similar work.
3. Entries record decisions **and the alternatives we rejected**, so future-us
   knows whether circumstances have changed enough to revisit.
4. Every entry ends with commit hashes + open items.

## Entries

| Date | Entry | What happened |
| --- | --- | --- |
| 2026-07-14 | [Strategy analysis & agent fixes](2026-07-14-strategy-analysis-and-agent-fixes.md) | Master-brief deep analysis (market reality check), fixed the broken conversational agent, built the chat test bench |
| 2026-07-15 | [Website build & review](2026-07-15-website-build-and-review.md) | "The black box was never black" site built, verified, shipped; ChatGPT review → claim-tightening pass |
| 2026-07-15 | [Approval dashboard](2026-07-15-approval-dashboard.md) | Next.js + shadcn dashboard, fail-closed remote approver, agent↔dashboard E2E |
| 2026-07-16 | [Dubai AI research](2026-07-16-research-dubai-ai.md) | KT article + DFF/WEF report deep-dive; found the regulatory goldmine (CR 56/2024, RERA); AI Seal action item |
| 2026-07-17 | [Community signals → product](2026-07-17-community-signals-and-buildout.md) | r/CRE research critique; built high-intent handoff, relationship policy, decision reasons, metrics sheet, live_chat, alternatives-on-demand |

## Key artifacts

- Product: `product-attesta/` (agent, Guard, Attesta core — 108 tests)
- Website: `website/` (static, GSAP, vendored)
- Dashboard: `dashboard/` (Next.js 16, port 3005)
- Pilot KPIs: [`PILOT-METRICS.md`](../PILOT-METRICS.md)
- Strategy: [`MASTER_BRIEF.md`](../MASTER_BRIEF.md) · research briefings in Vatsal's ATLAS dashboard

## Standing blockers (checked every entry)

- [ ] Real WhatsApp number on the website (`wa.me/971500000000` is a placeholder)
- [ ] Calendly/booking link for the demo CTAs
- [ ] Confirm `hello@leadcode.ae` receives mail
- [ ] Apply for the Dubai AI Seal (free, Dubai-licensed AI companies)
- [ ] **First outreach message sent** ← the one that matters
