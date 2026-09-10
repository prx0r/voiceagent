# THREADS.md — open threads per box (no confusion edition)

## Voice box (this repo) — owner: voice specialist
| # | Thread | State | Next action |
|---|---|---|---|
| V1 | Shared kernel schema lock | OPEN | Draft superset biz file both suites load (Phase 0) |
| V2 | Brain staging client (intake/slots/confirm + fallback) | OPEN | Needs brain staging URL |
| V3 | First live DID + Telnyx pilot call | BLOCKED | Credentials + $20 credits |
| V4 | TTS bake-off (Inworld Flash vs Cartesia) | OPEN | Env flag exists; needs ears (fal.ai) |
| V5 | Streaming STT + speculative graph prefetch | OPEN | Mocks model it; needs Deepgram key |
| V6 | Availability port (SlotProposal, anti-double-book) | OPEN | Port AIReceptionist pattern clean-room |
| V7 | S2S-vs-pipeline bake-off | OPEN | Needs DID; mocks run both shapes |
| V8 | Call outcomes → worth-it calibration feed | OPEN | Needs brain stats endpoint |
| V9 | EICR/gas-cert reminder calls (outbound) | OPEN | Needs pilot customer base |
| V10 | Free-checks-first graph upgrade + 105/network-fault branch | OPEN | Knowledge-only, no creds needed ← cheapest next win |
| V11 | Push stacked commits / merge PR | OPEN | Needs push token (revoke after) |

## Brain box (cmail — owner: other agent; tracked here so lanes don't collide)
| # | Thread | State (per their REVIEW-2026-09-10) | Voice dependency |
|---|---|---|---|
| B1 | Provider credentials (WA/Telnyx/Google OAuth, MX) | BLOCKED | Joint onboarding session covers V3 |
| B2 | Workers Paid $5 flip | OPEN | None |
| B3 | Pilot sparky | BLOCKED | Same human as V3 — one session |
| B4 | GCal live freebusy proof | OPEN | Unblocks V6 end-to-end |
| B5 | Social inbox→lead bridge | OPEN | None (voice-independent) |
| B6 | Second business onboarding | OPEN | Pairs with V-proofs of multi-tenancy |
| B7 | Outbound email send path | OPEN | None |
| B8 | Taxes lite (VAT + quarterly CSV) | OPEN | Our /sparky/export feeds it |
| B9 | SQLite→R2 nightly backup | OPEN | None (do before revenue) |

## Joint threads (both boxes, decide together)
J1 shared kernel schema · J2 bake-off metrics + verdict · J3 single onboarding script ·
J4 second-business proof · J5 EICR-amendment-2026 graph refresh (due 30 Nov 2026).

## Doc overlap map (highlight only — multiple paths are fine)
- REVIEW_2026-09-10.md → superseded by FINDINGS.md (kept for history).
- ARCHITECTURE.md (old channel vision) → ARCHITECTURE_SYNTH.md (current design).
- NEW_SPARKY_STACK.md → NORTHSTAR.md + DEV_PLAN.md (vision + order).
- VOICE_STACK → VOICE_ARCH_OPTIONS → FRONTIER_VOICE → STACK_SHORTLIST (research chain,
  newest last; conclusions stable across all four).
- UK_MARKET.md (numbers) + industries/ (law) + competition_and_horizon.md (rivals):
  complementary, read together.
