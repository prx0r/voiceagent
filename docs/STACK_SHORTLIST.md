# Stack shortlist: 3 integrated builds to test for quality (cloned + verified 2026-09-10)

All three run the SAME test: our 8 night-shift scenarios (scripts/simulate_calls.py
transcripts) placed as real calls. Score each on latency p50, grounding accuracy
(quotes graph, never invents), naturalness (blind listen), cost/min.

## Stack A — Official path (lowest risk)
pipecat-examples/telnyx-chatbot (Pipecat org, BSD-2): Telnyx TeXML inbound+outbound,
OpenAI LLM + Deepgram STT + Cartesia TTS. The reference implementation of our
VOICE_STACK.md decision. Test first; expect 500-800ms, best docs, zero license risk.

## Stack B — Grounded receptionist (closest to our vision)
torontodeveloper/voice-agent-chitti: Pipecat + Twilio + Deepgram + Silero + GPT-4.1 +
Cartesia + RAG knowledge + Railway deploy + deepeval tests. ⚠️ NO LICENSE FILE =
patterns only, do not paste; and RAG is Pinecone-hosted (swap for our YAML graph —
cheaper, offline, auditable). Test: does retrieval grounding survive the voice loop?
This answers our graph-over-voice question directly.

## Stack C — Full platform (fastest multi-channel demo)
amznsri/openvox (Apache-2.0 ✅): pipeline AND S2S modes with auto-fallback, Twilio +
WhatsApp (+QR sidecar) + Telegram, dashboard, 33 templates, skills+MCP, SQLite/PG.
Test pipeline-vs-S2S head-to-head on identical calls — settles the arch debate with
data instead of opinions.

## Bench tools (MIT ✅, vend freely)
- theopsio/ai-phone-caller: outbound Pipecat + cost table ($0.03-0.05/min) + SKILL.md
  onboarding. Steal the costing model and setup skill shape.
- sarmakska/voice-agent-starter: self-hosted adapter registries (STT/LLM/TTS) + e2e
  barge-in/tool tests + ARCHITECTURE.md state machine. Steal the bake-off harness:
  swap providers by env var, measure, pin winner.

## Research-grade (watch, don't build on)
Kyutai Moshi/Unmute (200ms full-duplex, needs L4 GPUs), Freeze-Omni + Tencent impl
(frozen Qwen2-7B S2S), DuplexOmni (Qwen3-Omni E2E training + vLLM serving, Apache-2.0
code but checkpoint/GPU-heavy), RelayS2S (81ms prefix + cascade verifier — phase-2
upgrade, code public). Revisit when a sparky's revenue pays for GPUs.

## License firewall
MIT/Apache/BSD (starter, ai-phone-caller, openvox, pipecat examples) = vendor with
attribution. NO LICENSE (chitti) + AGPL (AIReceptionist, sara) = read, reimplement,
never paste. Clones live in /tmp/opencode, never in this repo.
