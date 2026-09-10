# Voice architecture: 3 options, specced with measured numbers

Goal: read the graph instantly, talk naturally, minimal latency, minimal cost.
Key fact first: **the graph is never the slow part** — in-memory search is single-digit
ms. Latency lives in endpointing (150-500ms) + LLM first token (100-800ms) + TTS first
audio (20-250ms). So "instant graph read" is a property of WHEN you query (prefetch vs
prompt-stuffing), not query speed. Sources: Deepgram arch guide, Speko/Tianpan/Softcery
budgets, Presenc benchmarks, Inworld docs (all fetched 2026-09-10).

## Option 1 — S2S realtime (one model hears + talks)
E.g. OpenAI gpt-realtime-2.1 (native SIP), Qwen realtime (WS + gateway).
- Latency: ~500-900ms (gpt-realtime measured 494ms p50 conversational). Best feel:
  prosody preserved end-to-end, no transcript flattening, native barge-in.
- Graph read: prompt-injected context per session. Works while the graph is small; goes
  stale mid-call; NO audit of which fact grounded which sentence. Function calling
  exists but varies (Qwen WS contradictions documented in docs/QWEN_OMNI.md).
- Cost: highest. OpenAI $32/$64 per 1M audio tokens (mini $10/$20); long prompts and
  context re-bill. 60-min session cap.
- Reliability: black box — when it invents a price, you can't say which stage failed.
- PSTN: OpenAI native SIP = zero glue. Qwen/Gemini need LiveKit/Twilio gateway.
- Verdict: best conversation, worst accountability. Wrong for a business that quotes
  money and certs — unless sandboxed to chit-chat with tools doing the real work.

## Option 2 — Classic cascade (STT → graph → LLM → TTS, sequential)
What our /chat + edge_tts is today. Whisper batch + full-transcript graph search + full
LLM completion + file TTS.
- Latency: 800-2000ms. Walkie-talkie past ~1.5s; callers repeat themselves past 800ms.
- Graph read: EXACT and auditable — search runs on the final transcript, evidence IDs
  logged per turn (our evidence[] trail). Cheapest to run (small/local models OK).
- Cost: lowest per call; fully forecastable.
- Naturalness: flattest — transcript strips tone, batch TTS strips pacing.
- Verdict: reliable, cheap, provable — and too slow to feel human. The floor, not the
  ceiling. Every piece of it is reusable in Option 3.

## Option 3 — Streaming speculative cascade (recommended)
Deepgram Flux (STT+VAD+endpointing in one step, EagerEndOfTurn) → speculative graph
prefetch on partials → fast LLM (TTFT ≤200ms class) streamed token-by-token → Inworld
or Cartesia streaming TTS → barge-in with playback accounting.
- Latency: 500-700ms target. Budget: endpointing ~150-300 (semantic, not fixed silence)
  + STT absorbed in overlap + LLM prefill hidden inside endpointing window (speculative,
  +50-70% LLM calls) + TTS first audio 20-150ms + colocated hops ~50ms. Under the 800ms
  human-feel line; within striking distance of S2S.
- Graph read: TWICE per turn — silent prefetch on partials (warms evidence + tool args),
  confirmed search on final transcript (authoritative, audited). "Instant" because the
  answer's evidence is usually ready before the caller finishes speaking.
- Cost: near-Option-2 (small fast models, cheap fast TTS) + speculation overhead.
  Inworld Flash TTS down to ~$5/1M chars (~$0.005/min audio); STT $0.10-0.15/hr.
- Naturalness: best TTS voices in the world here (Inworld holds 3 of top 5 Artificial
  Analysis arena spots; Cartesia Sonic-3 ~40ms first audio). Slightly flatter than S2S
  on interruptions, fixable with playback-offset resume (Deepgram v2/speak Interrupt
  reports exactly what was heard vs unplayed).
- Reliability/audit: full — every stage logged, our guard + confirm-tokens unchanged.
- PSTN: Telnyx/LiveKit SIP in front; G.711 μ-law native. Co-locate STT+LLM+TTS in-region
  (60-140ms saved per hop).
- Build cost: real engineering (partial buffers, prefetch/discard, flush accounting) —
  but each upgrade ships independently: streaming STT → speculative prefetch →
  streaming TTS. No rewrite.

## Inworld specifically (you asked)
Easy graph fit: YES. Two integration shapes, both OpenAI-compatible: (a) Realtime TTS
as the TTS stage (WS streaming, 20ms Flash / 150ms flagship, steering, cloning,
Telnyx/Twilio SIP examples published); (b) Voice Agents Realtime API (STT→Router→TTS
managed session, sub-second, any LLM incl. ours, function calling + webhooks into OUR
graph/tools, SIP early access). SOC 2/HIPAA BAA, on-prem/VPC option. Pricing is
credit-metered ($25-$1500 tiers, Flash cheaper, enterprise to ~$5/1M). Caveats: SIP
still early-access (email for access), default 20 concurrent sessions, credit model
needs watching vs flat per-minute. Fits Option 3 as either the voice or the managed
session — graph stays our code either way.

## Decision
Build Option 3 on LiveKit-on-Telnyx (docs/VOICE_STACK.md), TTS = Inworld Flash or
Cartesia Sonic (pilot both, one env flag), STT = Deepgram Flux/Nova-3, LLM = fast small
(Kimi/Qwen3-235B/Spark) behind kernel tools. Keep Option 2 as the no-LLM fallback
(already working). Revisit Option 1 (OpenAI S2S + native SIP) as a premium tier when
call volume makes its premium worth it — behind the same guard/case kernel.
