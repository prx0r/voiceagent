# DEV PLAN — voice specialist track (ordered, dependency-gated)

## Phase 0 — Contracts (unblocks everything)
- [ ] V0.1: lock shared kernel schema with brain (one biz file both test suites load)
- [ ] V0.2: voice→intake + slots/confirm client against brain staging (timeout+fallback)
- [ ] V0.3: quote-preview verbatim-or-provisional rule enforced in prompts + tests

## Phase 1 — First live call (pilot)
- [ ] P1.1: Telnyx no-code assistant + DID on $20 credits (validates audio path)
- [ ] P1.2: deploy livekit_agent worker, dispatch rule, test call off-hours
- [ ] P1.3: joint onboarding session script (brain creds + voice DID, one 15-min call)
- [ ] P1.4: TTS bake-off (Inworld Flash vs Cartesia) behind env flag, measured p50/p95

## Phase 2 — Pipeline hardening (speculative cascade)
- [ ] P2.1: streaming STT (Deepgram Flux) + eager partials into graph prefetch
- [ ] P2.2: speculation rollback + barge-in playback accounting (mocks already model it)
- [ ] P2.3: availability port (SlotProposal, anti-double-book) against brain slots
- [ ] P2.4: S2S-vs-pipeline bake-off on shared metrics; loser becomes fallback tier

## Phase 3 — Voice feeding the stack (differentiation)
- [ ] P3.1: call outcomes → worth-it calibration feed (brain stats endpoint)
- [ ] P3.2: EICR/gas-cert reminder calls (outbound trunk + dispatch metadata)
- [ ] P3.3: spoken review requests post-job (review engine input)
- [ ] P3.4: second business onboarding (multi-tenancy proof both sides)

## Phase 4 — Scale prep
- [ ] P4.1: QR→Cloud API WhatsApp migration path for voice follow-ups (brain-owned)
- [ ] P4.2: retention cron in prod; SQLite→R2 backup story aligns with brain
- [ ] P4.3: cost dashboard per sparky (minutes, conversions, $/saved-job)

Gates: no phase starts until prior phase's metrics are logged (answer rate, bake-off
latency, verdict accuracy, false-wake rate). Credentials + pilot sparky block Phase 1;
nothing else does — everything else builds offline with mocks.
