# Lessons — mistakes made once, not twice

Consult before starting similar work. Newest last. Each lesson names the
mistake, what it cost, and the rule that prevents it.

**L1 · Never trust an uncommitted mental model of the code.** The 2026-07-14
"making agent better" commit referenced `template_converse`/`resolve_converser`
that were never written — the new agent crashed on import and had never run.
→ *Rule: run the test suite after every commit, especially AI-assisted ones.*

**L2 · Policy patterns must encode intent, not keywords.** The bare regex
`guarantee` blocked our own compliant disclaimers ("No guarantees, but…") —
the remediation loop could never converge. → *Rule: for every block-pattern,
test the false-positive (compliant text containing the word) AND the
false-negative (violation phrased without it).*

**L3 · A fallback must never masquerade as an answer.** `match_inventory`
padded empty results with random units, presented as "listings that fit" — an
instant credibility killer in front of a broker. → *Rule: when nothing
genuinely matches, say so / escalate; never fill the space.*

**L4 · Test with real user language.** `\binvest\b` didn't match "investment",
so "mainly investment" left leads unqualified. → *Rule: extraction tests use
the messy phrasing real leads type, not the tidy phrasing tests prefer.*

**L5 · Animation layers: viewport-sized, native scroll.** A 200%-size
transform-animated fixed grain layer + the Lenis scroll library wedged the
compositor (black screens). Removing Lenis and animating background-position
fixed it. → *Rule: no oversized composited layers; don't adopt libraries that
fight native scroll; animations are progressive enhancement.*

**L6 · The preview sandbox can't read ~/Desktop.** Dev servers launched via
launch.json get sandboxed from Desktop paths. → *Rule: serve static sites from
a /tmp staging dir (rsync after each edit); npm servers via `--prefix` work.*

**L7 · The browser pane can't screenshot scrolled positions**, and
programmatic scroll doesn't fire scroll events there. → *Rule: verify scroll
choreography programmatically (ScrollTrigger.update() + DOM state), screenshot
sections via `?noanim` + body-translate; it's a pane quirk, not a site bug.*

**L8 · Distinguish system failure from harness latency.** The first dashboard
E2E "failed" because drafts waited 180s for decisions I was too slow to give —
the system fail-closed rejecting them was CORRECT behavior. → *Rule: before
debugging a "failure", check whether a safety mechanism worked as designed.*

**L9 · Fan-out workflows die on rate limits — salvage, don't rerun.** The
deep-research run lost 69/100 agents to a session limit; the journal.jsonl
held complete claim extractions. → *Rule: read the workflow journal first,
re-verify only load-bearing claims yourself.*

**L10 · Protect the fast path.** "3 draft options by default" would triple
manager reading per decision and invite rubber-stamping. On-demand
alternatives kept approve-in-3-seconds intact. → *Rule: optionality belongs on
the unhappy path; the common case stays one-tap.*

**L11 · CLI flags drift from training data.** shadcn's `-b` now means base
library (radix|base), not base color; Next 16 params are Promises. → *Rule:
when a scaffold ships an AGENTS.md/docs, read it before writing code; pipe
`y` and pin versions when CLIs prompt.*

**L12 · Never let marketing outrun the cryptography.** "Show a regulator or a
court" and "independently verifiable" overclaimed what HMAC honestly supports;
an expert prospect would catch it. → *Rule: claims match the weakest link
shipped today; roadmap language for the rest. Credibility IS the product.*

**L13 · Read the report before citing it.** The DFF/WEF Top-10 contains ZERO
mentions of agentic AI — citing it as agentic-AI evidence would backfire in a
pitch. The gold was in different passages (audit/tampering language) found
only by reading all 49 pages. → *Rule: primary sources, always; grep before
you quote.*

**L14 · Port 3005 conflicts are usually our own dev server.** Kill the stale
`npm run dev` (schema changes need a restart anyway) rather than debugging.

**L15 · Research feels like progress; it isn't.** Two strong research passes
(Dubai AI, r/CRE) produced great material — and zero booked meetings. →
*Rule: every research block ends by naming the next SALES action, and the
standing blockers list gets checked in every journal entry.*
