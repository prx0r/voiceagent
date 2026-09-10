# LiveKit-on-Telnyx voice agent (scaffold)

Same LiveKit code as anywhere; Telnyx hosts it with carrier SIP built in.

## 0. Pilot shortcut (no code)
Telnyx portal → AI Assistant Builder → number → first call on $20 free credits.
Do this before deploying code.

## 1. Deploy this worker
```bash
pip install livekit-agents livekit-plugins-openai livekit-plugins-silero \
  "telnyx-livekit-plugin @ git+https://github.com/team-telnyx/telnyx-livekit-plugin.git#subdirectory=telnyx-livekit-plugin" httpx pyyaml
export TELNYX_API_KEY=... KERNEL_BASE_URL=https://your-kernel SPARKY_API_KEYS=<sparky-key>
lk agent create . && lk agent deploy . --secrets TELNYX_API_KEY=$TELNYX_API_KEY
```

## 2. Number + dispatch
Buy DID in Telnyx portal → point SIP connection at regional LiveKit SIP server →
dispatch rule routes calls to this agent. Outbound ("on my way", wake-call) via
outbound trunk + dispatch metadata (phone_number).

## 3. Swap parts (one line each in agent.py)
- STT: telnyx.STT() → deepgram Nova-3/Flux variant.
- TTS: VOICE_TTS=Telnyx.Ultra.Clara → Rime/ElevenLabs BYOK / Qwen3TTS.
- LLM: VOICE_LLM=kimi → Qwen3-235B / GPT-4o-mini / Claude BYOK.
Kernel tools stay identical — the voice layer never holds prices or policies.
See requirements.txt (plus the telnyx plugin git URL inside it).
