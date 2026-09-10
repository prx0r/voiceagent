# Voice stack decision (2026-09-10) — phone agents for UK trades

## Verdict: Qwen Omni is fine, but not optimal for PSTN. Go pipeline on Telnyx.

Qwen stays in the stack (LLM and/or TTS), just not as the realtime speech-to-speech mouth.

## Why not Qwen realtime as the mouth
- WS-only: still needs a LiveKit SIP gateway for PSTN — same glue as everyone else.
- Docs contradict themselves on WS function-calling; HTTP-only tools in places.
- Token billing + DashScope region-locked keys.
- Less pipeline visibility than a staged stack (we need transcripts-for-audit: what the
  caller said vs what the model heard vs what it said — our case file depends on it).

## Optimal stack (production)
- Transport/compute: **LiveKit Agents on Telnyx** — same LiveKit code, carrier SIP
  built in (no third-party SIP fees, HD G.722/Opus), colocated GPUs ~2ms, one bill.
  $20 free credits; `lk agent deploy` path documented.
- STT: **Deepgram Nova-3** via telnyx plugin (3.5% WER clean / 9% noisy, keyword
  boosting for "consumer unit", "Ohme", "EICR"; interim results for barge-in).
- LLM: cheap + fast via Telnyx inference (`Kimi-K2.5`/GLM class or Qwen3-235B) behind
  our kernel tools (function_tool → qualify/triage/book/calendar/parts). Brain stays
  swappable; Muse Spark via Model API remains an option for wording quality.
- TTS: **Qwen3TTS** or Telnyx Ultra / Cartesia Sonic (~80-120ms first audio) /
  ElevenLabs BYOK for premium cloned voice. UK voice shortlist at pilot.
- VAD/turn: Silero + server VAD; BVC telephony noise cancel on SIP leg.
- Numbers: Telnyx DID → SIP → dispatch rule → agent room. Outbound ("on my way",
  wake-call) via outbound trunk + dispatch metadata.

## Pilot path (this week, ~5 min)
Telnyx no-code AI Assistant + number → first real call on $20 credits. Validates audio
quality + greeting + transfer before writing agent code. Vapi/Retell configs import if
we prototype there first.

## Rejected / deferred
- OpenAI Realtime + native SIP: best conversation (400-600ms), zero media glue — but
  $32/$64 per 1M tokens, 60-min cap, no published concurrency/SLA, token billing punishes
  big system prompts. Revisit as premium tier when volume pays for it.
- Gemini Live: 10x cheaper tokens, 97 langs, fastest first audio — but re-bills full
  context every turn, ~10-min socket resets, 15-min sessions, NO SIP. Integration tax
  kills it for phone. App/browser only.
- Grok Voice ($0.05/min flat, cloning): watch; immature ecosystem.
- Nova 2 Sonic: contact-center king, 7 langs — wrong coverage for UK trades.
- Vapi/Retell/Bland managed: fastest launch (500-900ms) but platform rent + data/export
  control; Telnyx imports their configs, so prototype there, land on Telnyx.

## Unit economics sanity (per sparky, ~40 after-hours calls/mo, ~3 min avg)
- Telnyx agent $0.05/min → ~$6/mo + DID (~$1-2) + WA sends. One saved job (£65 callout
  minimum) pays ~10 months. Deepgram-direct pipeline similar. OpenAI Realtime ≈ 5-10x.
