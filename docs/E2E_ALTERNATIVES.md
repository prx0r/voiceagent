# E2E alternatives scorecard (2026-09-10, this box: no provider keys, no DID, 7GB disk)

Log: var/e2e_kernel.log (ours, 15/15). Others below = deepest verification possible keyless.

## Stack O — ours: FULLY EXECUTED ✅
- 34/34 unit tests + scripts/e2e_kernel.py 15/15 (qualify→book→wake/queue→digest→
  act→feed→export→retention). Only stack runnable end-to-end here, and the only
  one with graph grounding + guard + audit on every turn.

## Stack A ref — pipecat telnyx-chatbot: STATIC ✅ / LIVE ❌ (needs keys+DID)
- Inbound+outbound bots compile clean (124-line inbound: Deepgram+OpenAI+Cartesia,
  TeXML). Needs OPENAI+DEEPGRAM+CARTESIA keys + Telnyx number. Verdict: credible
  live-call route, unverified audio. First thing to run when keys land.

## Stack B ref — chitti: STATIC ✅ / LIVE ❌ + LICENSE ⚠️
- bot.py/main.py/ingest.py compile; RAG is hosted Pinecone (cost + dependency).
  NO LICENSE FILE = patterns only, never paste. Railway deploy + deepeval tests
  present but need keys to run.

## Stack C — openvox: 86 TESTS GREEN KEYLESS ✅ / LIVE ❌
- test_text_helpers + portutil (56) + providers/skills/templates (30) all pass with
  mocked HTTP. Apache-2.0. Deepest independently-verified base after ours. Live
  calls need providers + numbers. TTS/STT/s2s_bridge suites need keys — not run.

## Bench (MIT ✅)
- voice-agent-starter: 37/37 vitest keyless (adapters, barge-in, tool passthrough).
  Best bake-off harness shape.
- ai-phone-caller: structure + env verified (Twilio/Telnyx dual), compiles. Needs keys.

## Research S2S (Moshi/Unmute/Freeze-Omni/DuplexOmni): NOT RUNNABLE HERE ❌
- Needs GPUs + multi-GB checkpoints; disk 91% full makes it infeasible by
  construction. Revisit on revenue-funded infra.

## Honest bottom line
No live audio was compared anywhere — impossible without keys/DID. Stack ranking on
call quality is NOT empirically settled. Settled: (1) ours is the only fully
executable + grounded stack here; (2) openvox has the deepest verified test base;
(3) pipecat-telnyx is the documented route to first live call. Next: $20 Telnyx
credits + 3 keys → run the 8 night-shift scenarios as REAL calls on A and C, score,
then decide. Also: this box bit us once today (stray sparse-checkout hid tracked
files; recovered via disable, 34/34 re-verified) — run telephony pilots from /tmp.
