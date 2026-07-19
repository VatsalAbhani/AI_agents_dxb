# 2026-07-14 — Strategy analysis & agent fixes

## Context
Vatsal shared the MASTER_BRIEF and asked for a thorough analysis; then asked to
check the Cursor-made "making agent better" commit (5c790e2) and test the agent
before cold approaches.

## What we did
1. **Strategy analysis** (verified the repo first-hand: 55 tests passing).
   Key conclusions, evidence-backed via web research:
   - Competitive scan in the brief was already stale: Glacis (funded, "flight
     recorder for enterprise AI"), Vorlon shipped Flight Recorder + Action
     Center at RSA 2026, OSS clones (halo-record) commoditising the ledger.
   - Payments destination: receipts are being built INTO the rails (Google AP2
     signed mandates, Stripe/OpenAI ACP, Coinbase x402 ~165M txns, AWS
     AgentCore Payments) → realistic play = neutral cross-rail evidence layer.
   - **The strategic knot:** the SMB wedge doesn't compound toward developer
     infra. Discipline test: does any client buy BECAUSE of the audit trail?
   - HMAC seal cannot honestly be marketed "cryptographically verifiable"
     (symmetric key-holder can forge) → say "tamper-evident" until Ed25519 +
     anchoring ship.
   - 90-day rule set: 3 paid pilots; no new idea evaluations before then.
2. **Agent fixes** — the Cursor commit was incomplete/broken (L1):
   - Wrote missing `template_converse`/`resolve_converser`/LLM converser +
     sample inventory.
   - Fixed: blocked drafts polluting conversation history; `guarantee` regex
     blocking disclaimers (L2); fake inventory-fallback matches (L3);
     `\binvest\b` missing "investment" (L4).
   - Built `examples/chat_test.py` interactive bench (play lead + manager).
3. Verified: 77 repo tests + 23-check stress suite (incl. actual ledger
   tampering detected), all demos, mock-LLM mode.

## Decisions & rejected alternatives
- **Keep flight-recorder positioning for brand story only**, sell
  "approval + audit" (rejected: leading sales with the crypto ledger).
- Narrowed policy regexes to promise-forms rather than adding an LLM judge now
  (human-approval catch-all is the real safety net for pilots).

## Outcome
Working, tested agent; strategy risks named; pilot discipline set.
Commits: `ad99466` (Vatsal pushed the fixes bundled with the website).

## Open items → carried forward
LLM key not set (agent runs offline template); real-LLM testing before pitches.
