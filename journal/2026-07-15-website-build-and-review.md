# 2026-07-15 — Website build & review pass

## Context
Vatsal: creative, timeless, non-generic site — "wow, these people are smart."

## What we did
1. **Concept: "The black box was never black."** Flight recorders are
   international orange → ink/paper/orange palette, Instrument Serif +
   Instrument Sans + IBM Plex Mono. Static HTML/CSS/JS, GSAP + ScrollTrigger
   vendored (168KB total, no build step). Location: `website/`.
2. Signature sections: hero with hash-ticker; scroll-pinned **chat-vs-ledger
   theatre** (Guard blocks "guaranteed 20%" mid-conversation, rewrite approved,
   run sealed); interactive **"try to rewrite history"** tamper widget with
   honest cascade; full-orange manifesto; cream pilot offer (AED 12,500);
   FAQ; outro.
3. **Debug saga (L5–L7):** compositor blackouts → bisected grain layer, killed
   Lenis, moved staging to /tmp (sandbox), added `?noanim` QA mode +
   `window.__guard.render(n)` hooks; verified all sections via body-translate
   screenshots + programmatic ScrollTrigger checks; mobile pass.
4. **Review pass** (ChatGPT scored it 8/10; its 3 hard hits matched my own
   flags): dropped court/regulator claim, "independently verifiable" →
   "tamper-evident", honest FAQ wording, softened 78% → "Most", "not a
   chatbot" moved up, 14-day checklist, "who this is for", footer contact,
   eyebrow now "MANAGER APPROVAL · AUDIT TRAIL" (flight recorder stays in the
   manifesto). Pushed back on flattening "Evidence can't" → kept punch with
   accuracy: "This one shows the break."

## Decisions & rejected alternatives
- Static site over Next.js (timeless, deployable anywhere) — dashboard is
  where the framework lives.
- Rejected component libraries for the marketing site (genericide); reserved
  shadcn/21st.dev for product UI.

## Outcome
Commits: `ad99466` (build), `d7d93c3` (claim-tightening).
Preview: launch.json `guard-website` → serves /tmp staging (rsync after edits).

## Open items
WhatsApp number, Calendly, email confirmation (standing blockers).
Deployment to a live URL — not yet done.
