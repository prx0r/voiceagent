# TTS bake-off spec (figures verified 2026-09-10; ears decide, not specs)

Candidates: Cartesia Sonic 3.5 (Turbo ~40ms, standard sub-100ms, 42 langs, Line
telephony built in) vs Inworld 1.5 Mini/Max (Mini ~120ms P90, Max sub-200ms, AA arena
#1 quality, STT-1 2.2% WER, full pipeline+router) vs Qwen3-TTS (fal $0.07-0.09/1K).
Caveats (Coval 2026): vendor P50s hide tails — Cartesia median measured 188ms in prod;
no shared benchmark covers both; decide by blind A/B on OUR audio (Dan's lines, 8kHz
phone profile, UK accents), P95 + MOS + £/1K chars.

Protocol: same 10 utterances (greeting, quote range, safety warning, slot offer) × each
voice → rank naturalness blind, record P95 first-audio, compute cost at 40 calls/mo.
Winner pinned behind TTS_PROVIDER; loser stays as fallback. Also test blended tiers
(premium for greetings/bad-news, mid for routine) if volume justifies.
