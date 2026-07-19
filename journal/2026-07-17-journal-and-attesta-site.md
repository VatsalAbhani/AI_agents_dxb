# 2026-07-17 (later) — Journal system + Attesta company site

## Context
Vatsal's standing directive: record everything (→ this journal, memory rule,
LESSONS.md). Then "build a website for our startup" — ambiguous since the
Guard site exists; asked; answer: **a NEW site for Attesta, the company/
infrastructure brand** (developers, partners, investors). Guard site stays
for Dubai clients.

## Design decision
**Concept: "The Evidence File"** — inverts the Guard site: warm paper,
mono-led type (IBM Plex Mono display), hairline ruled-paper texture, orange
used ONLY as the verification seal. Same family DNA, opposite polarity.
Rejected: reusing the dark/serif direction (would blur the two brands);
component libraries (genericide, same as before).

## What we built (`website-attesta/`, static + vendored GSAP)
- Hero: mono RECORD/VERIFY/REPLAY/PROVE + **self-verifying ledger** — hashes
  scramble → settle → ✓ cascade → orange INTACT seal stamps (timer-based, so
  it even survives rAF throttling; noanim/reduced-motion → final state).
- §01 problem (reproduce/prove/control) · §02 four primitives grid ·
  §03 real Python + auto-typing `attesta verify` terminal · §04 "What we
  won't claim" honesty section (no bit-for-bit replay; HMAC v0 stated
  plainly — L12 applied proactively) · §05 Guard bridge card (ink block on
  paper, links `/guard/`) · §06 receipts destination · footer.
- Serve: port 4199, /tmp staging (L6); **Guard site staged under `/guard/`**
  so the cross-link works and single-domain deployment is trivial.

## Mistakes & fixes
- Guard link was `../website/index.html` (would 404 deployed) → `/guard/`.
- Grid blowout: `pre` min-content width pushed codeblocks to 533px on a
  375px viewport → `.codeblock { min-width: 0 }`. (New lesson candidate:
  grid children holding `pre`/tables always need min-width:0.)
- Pane rAF throttling made GSAP tweens crawl in background tab — verified
  via computed opacity + noanim pass instead (L7 held).

## Outcome
Verified desktop + mobile (no overflow), both URLs 200 on preview.
Commit: (this commit). Journal system: commit `ff603a6`.

## Open items
- Deployment: not yet live — candidate: here.now (Vatsal's permanent
  account, like Hudood) with attesta at `/` and guard at `/guard/`, or two
  separate slugs; needs Vatsal's go.
- Standing blockers unchanged: WhatsApp · Calendly · email · AI Seal ·
  first outreach.
