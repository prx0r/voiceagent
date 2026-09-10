# Qwen Omni — imported notes (checked 2026-09-10, QwenCloud docs)

Source: https://docs.qwencloud.com/developer-guides/speech/s2s-models
+ realtime-multimodal-speech + client-events + Python SDK pages.

## Which model for our voice agent
- Realtime voice assistant WITH tool calls over WebSocket: **`qwen-audio-3.0-realtime-plus`**
  (cheap alt: `qwen-audio-3.0-realtime-flash`). These are the only series where
  docs guarantee WS function-calling today.
- `qwen3.5-omni-plus-realtime` / `-flash-realtime`: richer (audio+image+video in,
  29 output langs, web search, semantic VAD) BUT docs contradict themselves on WS
  function-calling — model table says ✓, companion-capabilities section says WS
  realtime does NOT support it (HTTP only). Do not architect as if WS tools are
  guaranteed on 3.5-Omni. Our kernel routes tools server-side anyway, so either
  model works: tools are executed by OUR code from transcripts, never trusted
  from the model alone.
- **Function calling and web search are mutually exclusive** on Omni. We always
  run tools-mode (search off). Parts prices come from our suppliers table, not
  model search — quotable and auditable.

## Wire protocol (correct — our first adapter draft had the wrong URL)
- Endpoint: `wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=<name>`
  (region-locked keys: `-intl` vs mainland `dashscope.aliyuncs.com`).
- Auth: `Authorization: Bearer <DASHSCOPE_API_KEY>`.
- First message must be `{"event_id": ..., "type": "session.update", "session": {...}}`
  with `modalities: ["text","audio"]`, `voice`, `input_audio_format: "pcm"`,
  `output_audio_format: "pcm"`, `instructions`, `turn_detection:
  {"type":"semantic_vad"|"server_vad","threshold":0.5,"silence_duration_ms":800}`.
- Audio: PCM 16kHz mono in (base64 `input_audio_buffer.append`), PCM 24kHz out.
  Telephony is 8kHz — resample 8k→16k in, 24k→8k out (see 3CX build below).
- Tool results return via `conversation.item.create` with
  `item: {type: "function_call_output", call_id, output: "<string>"}`, then
  `response.create`. VAD mode auto-responds otherwise.
- Python SDK (`dashscope>=1.25.17`):
  `from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback` —
  `conv.connect()`, `conv.update_session(output_modalities=[...], voice=...,
  instructions=..., tools=[...])`, `conv.append_audio(b64)`,
  callbacks: `response.audio.delta` (play), `...input_audio_transcription.completed`
  (caller text), `response.function_call_arguments.done` (tool call).

## Related builds worth copying
1. **3CX + Qwen realtime** (`3cx/agentic-call-control`, `examples/alibaba-qwen-realtime/`):
   PSTN→3CX→single Qwen WS, no STT/LLM/TTS pipeline. Tool executor splits local
   tools (transfer/drop/voicemail/screening) vs MCP tools (incl.
   `googlecalendar.quick_add`). Barge-in free via server VAD. This is our PSTN
   template: replace 3CX with LiveKit SIP or Telnyx when ready.
2. **Next.js + Cloudflare Workers** (qwen3omni.net tutorial): browser AudioWorklet
   (16kHz int16) → WS → Durable-Object session → Qwen stream → text+audio back.
   Our `static/` demo follows the same shape minus the edge worker.
3. **Our stack**: LiveKit rooms already in `app/session.py` for app-voice;
   SIP/Telnyx attaches at LiveKit layer later. Qwen is the mouth/ears,
   `app/graph.py` + `app/guard.py` + confirm-tokens stay the brain.

## Production voices
- 3.5-Omni realtime default `Tina`; flash `Cherry`; audio-realtime series has own
  list. Preset via `voice`; cloning only on 3.5-Omni realtime via Voice Cloning API.
  Tradie/receptionist presets live in `knowledge/*.yaml` voice blocks.
