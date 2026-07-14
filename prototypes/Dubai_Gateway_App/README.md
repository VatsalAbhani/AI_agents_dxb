# The Dubai Gateway — Funnel Pressure-Test (MVP)

A working top-of-funnel to **test the wedge for real**: an attractive landing page + two lead-magnet
tools (ROI calculator, Golden-Visa checker) + qualified lead capture, plus a **founder dashboard** that
computes **cost-per-qualified-lead (CPQL)** and lights up the instant it beats the AED 100k+ commission
per deal.

The whole thesis is one comparison: **what it costs to get a serious buyer in front of you vs. what one
closed deal pays you.** This app makes that comparison measurable.

---

## Run it

No install, no internet:

1. Keep `index.html` and `funnel.js` **in the same folder**.
2. Open `index.html` in any browser.
3. Two modes, switched with the **📊 Founder view** button (top-right):
   - **Public site** — what a prospect sees: hero, projects, ROI calculator, Golden-Visa checker, and the "Talk to us" form that **qualifies** each lead (Hot / Warm / Cold).
   - **Founder view** — the pressure-test: move the sliders (spend, CPL, conversion rates, ticket, commission) and watch **CPQL, CAC/deal, ROAS, break-even CPQL** and a **profitable / not-yet verdict** update live. Plus a table of every lead the funnel captured.

Try it: submit the public form a few times, then open **Founder view → Load sample leads**.

---

## The one number that matters

> **Break-even CPQL = commission per deal × (qualified → close rate).**

At the research-grounded defaults (AED 30k spend, AED 250 CPL, 25% qualify, 6% close, AED 2.7M ticket,
5% commission):

| Metric | Value |
|---|---|
| Commission per closed deal | **AED 135,000** |
| Cost per qualified lead (CPQL) | **AED 1,000** |
| Break-even CPQL | **AED 8,100** |
| Headroom | **~8×** |
| ROAS | **~8×** |

Translation: you could pay **8× more** per qualified lead and still break even. That headroom is exactly
why a founder with **no network** can win this — you don't need virality, you can *buy* high-intent global
traffic profitably.

---

## How to run a REAL test (the point of this)

1. **Ship the landing page** (host `index.html` — Netlify/Vercel/Cloudflare Pages, free).
2. **Wire the form** to a real destination (see roadmap) so leads reach you.
3. **Buy a little traffic** — a small Google/Meta campaign (AED 3–10k) targeting ONE nationality + intent
   (e.g. "buy Dubai property from India", "Dubai Golden Visa"). Send clicks to the ROI/Visa tools.
4. **Measure two things** from real data:
   - **Actual CPL** = ad spend ÷ leads captured.
   - **Actual lead → qualified %** = qualified leads ÷ total leads (the app scores this for you).
5. **Plug your real numbers** into the Founder view. Read the verdict.

**Decision rule:** if your real **CPQL stays comfortably below break-even** (AED ~8k at a 6% close) *and*
you can secure developer commission agreements, the wedge is validated — pour fuel in. If CPQL is near or
above break-even, fix the funnel (better creative/targeting, tighter qualification, higher close rate)
before scaling.

---

## What's real vs. illustrative

- **Real:** all the math — ROI, Golden-Visa thresholds, lead scoring, and the full funnel economics
  (unit-tested in `test/funnel_test.js`, 20 checks; UI verified in `test/ui_smoke.js`, 16 checks).
- **Illustrative / to replace before launch:** the 3 featured projects and the sample leads are demo data;
  area yields and visa thresholds are directional (confirm with DLD/RERA & GDRFA/ICP); there is **no
  backend** — captured leads live in your browser's local storage.

## Files

```
Dubai_Gateway_App/
├─ index.html        Landing page + tools + lead capture + founder funnel dashboard
├─ funnel.js         Engine: ROI, Golden-Visa, lead qualification, funnel economics (browser + Node)
├─ README.md         This file
└─ test/
   ├─ funnel_test.js  20 unit checks (calculators + economics + break-even)
   └─ ui_smoke.js     16 end-to-end UI checks (jsdom)
```

```bash
node test/funnel_test.js
npm i jsdom && node test/ui_smoke.js
```

## Roadmap to a live test (small, fast)

1. **Form → destination:** POST leads to a Google Sheet / Airtable / email / CRM (a few lines).
2. **Analytics + pixels:** GA4 + Meta/Google conversion pixels so CPL/CPQL are measured automatically.
3. **Real inventory:** replace demo projects with live developer feeds + real commission agreements.
4. **Multi-language funnels:** duplicate for Hindi / Russian / Chinese / Arabic audiences.
5. **Booking/nurture:** WhatsApp + calendar so qualified leads convert while intent is hot.

*Illustrative figures throughout. Not financial or legal advice. Property and visa rules must be confirmed
with the relevant UAE authorities.*
