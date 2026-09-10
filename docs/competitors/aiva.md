# Aiva (7XLabs/Aiva) — MIT open-source analog (cloned /tmp/opencode/aiva, verified)

Next.js + Claude Opus 4.8 tool loop + Twilio Voice. Closest open codebase to our kernel
philosophy: "The model is never trusted — every state-changing tool re-validates"
(bookings re-check slot at write time = our confirm-token + anti-double-book instinct).

## Worth stealing (MIT ✅)
- lib/agent: bounded tool loop (windowed history, error fallback, language propagation),
  11 validated tools, prompt built from business KB.
- lib/insights (per-call analysis: summary/sentiment/intent/action items) + lib/digest
  (cross-call business reports) = our brief/digest split, production-shaped.
- Caller memory by number; action-item queue (callback/follow-up task list); SMS layer
  with dedup + next-day reminders; analytics dashboard; live KB editing (next call knows).
- 16 test files (slots, overlap/double-book, twiml, rate-limit, tools, languages…).
- Business import/export endpoints (multi-tenant portability); docs/API + WEBHOOKS + FAQ.
- 8+ languages with mid-sentence switching.

## Gaps vs us (why we still build)
Twilio-only telephony (no Telnyx/SIP path), Claude-only brain (no provider flip), no
trade vertical (clinics/salons/restaurants), no urgency triage ladder, no parts/jobs
scoring, no retention story stated, no speculative-cascade work. Take the guardrail +
insights + test patterns; keep our kernel.
