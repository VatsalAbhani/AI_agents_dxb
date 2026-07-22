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
| 2026-07-17 | [Journal system + Attesta site](2026-07-17-journal-and-attesta-site.md) | This journal established; new Attesta company site ("The Evidence File" — paper/mono, self-verifying ledger hero) built and verified |
| 2026-07-18 | [Agent service + review fixes](2026-07-18-agent-service-and-review-fixes.md) | Restart-proof agent service (intake→turns→approvals→sealed ledgers, 14 tests, live E2E); dual-site review fixes incl. the verification-wording contradiction |
| 2026-07-21 | [LAUNCH](2026-07-21-launch-deployment.md) | Everything deployed to Railway with real Claude; production E2E sealed INTACT; sites live with real WhatsApp + Calendly |
| 2026-07-22 | [Broker feedback video](2026-07-22-broker-feedback-video.md) | 60s vertical video built with Chrome+WebCodecs (no ffmpeg): real product frames, real Claude refusal; send-kit in outreach/ |

## Key artifacts

- Product: `product-attesta/` (agent, Guard, Attesta core — 108 tests)
- Website: `website/` (static, GSAP, vendored)
- Dashboard: `dashboard/` (Next.js 16, port 3005)
- Pilot KPIs: [`PILOT-METRICS.md`](../PILOT-METRICS.md)
- Strategy: [`MASTER_BRIEF.md`](../MASTER_BRIEF.md) · research briefings in Vatsal's ATLAS dashboard

## Standing blockers (checked every entry)

- [x] Real WhatsApp number on the website (+971 56 960 2690, live)
- [x] Calendly/booking link wired into all demo CTAs
- [x] LLM key + hosting — DEPLOYED, real Claude in production
- [ ] Confirm `hello@leadcode.ae` receives mail
- [ ] Upgrade Railway Trial → Hobby (services die when the $5 credit runs out)
- [ ] Apply for the Dubai AI Seal (free, Dubai-licensed AI companies)
- [ ] **First outreach message sent** ← the one that matters
