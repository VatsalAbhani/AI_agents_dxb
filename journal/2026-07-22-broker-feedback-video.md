# 2026-07-22 — The broker feedback video (made without a video tool)

## Context
Vatsal asked for a video to send brokers for feedback. Higgsfield connector
session expired (needs re-auth in claude.ai settings for a narrated v2), so
built it locally: **Chrome as renderer AND encoder** — no ffmpeg (won't
side-load unsigned binaries), no video SaaS.

## Method (reusable pipeline — outreach/video-src/film.html)
1. Filmed a REAL conversation: local service + real Claude; the lead demanded
   "guarantee me 20% returns" — Claude refused in writing. That refusal IS
   the film's centrepiece, verbatim.
2. Screenshots via headless Chrome at 3x. Discovered + fixed a REAL mobile
   bug on camera: the HIGH-INTENT badge never wrapped (min-content width blew
   the layout past the viewport) — badge shortened + whitespace-normal; chat
   bubbles viewport-capped.
3. Rendering: canvas scene engine (10 scenes, 59.5s, 1080x1920) encoded with
   **WebCodecs VideoEncoder + mp4-muxer** — explicit frame timestamps, immune
   to the timer throttling that broke MediaRecorder (86s "3-second" probe).
4. QA via scene-still preview grid (video-decode contact sheets fail in
   headless). Caught: mojibake (film.html had no charset meta → ·/✓ corrupted
   INSIDE the encoded video), pan overrun, zoom crop. Fixed, re-rendered.

## Lessons for LESSONS.md (candidates, folded here)
- Headless window-size ≠ CSS viewport (min width 500, titlebar -87px) —
  probe innerWidth before designing captures.
- Real-time recording (MediaRecorder) is unusable under throttling; WebCodecs
  with explicit timestamps is the deterministic path.
- Always <meta charset> in generated pages — mojibake burned into video.
- Screenshots of the product are free QA: two real mobile bugs found.

## Deliverables
- ~/Desktop/guard-feedback-video.mp4 — 59.5s, 9:16, H.264, 29.9MB,
  captions-first (WhatsApp muted viewing)
- outreach/whatsapp-feedback-message.md — the send-kit
- outreach/video-src/ — full source; edit film.html scenes + re-run to remix

## Standing blockers
Railway Hobby upgrade · email check · AI Seal · **now: press send.**
