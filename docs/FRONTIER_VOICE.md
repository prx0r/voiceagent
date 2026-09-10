# Frontier voice stack (arXiv + GitHub + fal.ai, 2026-09-10)

## arXiv consensus: cascades + speculation are the frontier, not S2S
- Endpoint Anticipation (2606.13450): speech-only EOT forecast 2.56s ahead, −505ms,
  +28% compute, Unmute integration, open-sourcing. Our prefetch idea, peer-reviewed.
- RelayS2S (code: mailong25/relays2s): duplex-S2S fast path drafts spoken prefix
  (P90 onset 81ms!) + cascaded slow path continues via verifier gate, 99% quality.
  Drop-in, no arch change. = Phase-2 upgrade path for us.
- DuplexCascade: VAD-free 0.6s micro-turns + LLM control tokens, LoRA 5k steps,
  SOTA open turn-taking, Qwen2-7B backbone. = turn-taking upgrade path.
- PredGen (~2x cut, pre-synthesize first sentence), LTS-VoiceAgent (semantic trigger
  + background Thinker/foreground Speaker — our worth-it/plan split, formalized),
  DDTSR (small-large synergy, −19-51%, plug-and-play, code public), FastTurn (robust
  turn detection in noise). LTS explicitly benchmarks cascades vs Qwen2.5-Omni E2E —
  cascades win quality, E2E wins onset. RelayS2S takes both.

## GitHub: Pipecat (14k★, BSD-2) is the de-facto pipeline framework
Frame pipeline, 500-800ms typical, and it already ships OUR design: SpeculativeUser-
Aggregator (eager-end → speculate, resume → rollback), SemanticTurnDetection,
interruption_strategy blocking barge-in during non-idempotent tools (= our confirm
tokens), function calling with pre-tool speech ("Let me check that"), Telnyx
serializer + WhatsApp transport native, Qwen/Inworld/Cartesia/Deepgram all pluggable,
Pipecat Cloud or self-host. LiveKit Agents stays valid for carrier-billed Telnyx path;
Pipecat wins on pipeline expressiveness. Recommendation: prototype pipeline in Pipecat
(keeps LiveKit transport option open), deploy where billing/ops says.

## fal.ai: the TTS bake-off rig (one-line swaps, pay-as-you-go)
Per 1K chars: Chatterbox $0.025 → ElevenLabs Turbo $0.05 → Qwen3-TTS 0.6B $0.07 →
Qwen3-TTS 1.7B $0.09 → MiniMax HD $0.10. Voice Design + Clone endpoints (Qwen3-TTS,
MiniMax, Lux). Streaming supported. Use fal to blind-test 3 voices on Dan's lines,
then pin the winner natively (fal queue adds variance — bake-off there, serve direct).

## Qwen verdict (thesis check): YES as components, NO as the mouth
For: Qwen3-TTS (design+clone, on fal AND Telnyx), Qwen LLMs as cascade backbones
across papers (2.5-0.5B/7B, Qwen2-7B DuplexCascade), Qwen2.5-Omni as E2E reference.
Against (as realtime S2S mouth): papers use it as baseline not best; top onset numbers
belong to hybrids; WS tool docs contradict; region-locked keys. Keep Qwen3-TTS +
Qwen LLM in the matrix. Don't bet the mouth on Qwen Omni realtime.

## Graph structure (maps to frontier)
Now: YAML entities/edges + TF-IDF (ms lookups — never the bottleneck). Prefetch on
partials + confirm on final = PredGen/LTS pattern, already our design. Next: Stream-RAG
style tool-calling over partials; pgvector semantic recall past ~100 nodes; background
Thinker maintaining plan/state while Speaker talks (LTS dual-role = our digest/worth-it
split, moved into the call).

## Pinned stack (ordered)
1. Pipecat pipeline (BSD-2), Telnyx serializer for PSTN, WhatsApp transport for msgs.
2. STT: Deepgram Flux (EoT built-in) → Nova-3 fallback; Fal Wizper in bake-off.
3. LLM fast: Qwen3/Kimi/Gemma-class, TTFT ≤200ms; background Thinker for plan.
4. TTS: blind bake-off on fal (Qwen3-TTS vs ElevenLabs Turbo vs MiniMax vs Inworld
   Flash), pin winner native; Inworld favored on quality-per-dollar curve.
5. Turn: semantic trigger now; micro-turns + RelayS2S prefix drafter phase 2.
6. Deploy: Telnyx carrier billing (LiveKit-on-Telnyx or Pipecat+Telnyx serializer).
