# Voice / channel adapters

Default MVP uses Edge TTS only for browser playback. The business layer is deliberately independent of speech transport.

Recommended production swaps:

- **LiveKit Agents + LiveKit SIP**: preferred if you want to own session/telephony state and swap STT/LLM/TTS providers.
- **Pipecat**: very composable frame pipeline; good when you need low-level interruption/VAD/provider control.
- **Bolna**: useful reference for hosted-style STT→LLM→TTS orchestration over WebSockets with Twilio/Plivo.
- **TEN Framework**: strong alternate realtime multimodal/SIP architecture.
- **Retell/Vapi**: fastest managed launch; keep tool/graph state in this kernel, not inside provider prompts.
- **Inworld TTS**: swap into a `synthesize(text, locale)` adapter; keep the API contract identical.

Production rule: telephony-verified caller identity is authoritative. Never let an LLM overwrite trusted phone/account identity extracted from transport/auth.
