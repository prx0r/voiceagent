"""Mock voice providers. NO audio, NO network — deterministic script playback.

Each mock mirrors the real provider's CONTRACT (method names, chunk shapes,
timing fields) so pipeline code written against mocks ports to Deepgram/
Cartesia/Telnyx by swapping the class. Simulated ms values come from the
measured budgets in docs/VOICE_ARCH_OPTIONS.md (Deepgram/Speko numbers) and are
LABELED simulated everywhere — mocks prove wiring/behavior, never audio quality.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# Simulated stage budgets (ms), from published production measurements.
STT_PARTIAL_MS = 150      # streaming first partial (Deepgram Nova-3 class)
ENDPOINT_MS = 280         # semantic end-of-turn (not fixed-silence 500+)
EAGER_MS = 120            # eager-end fires this much before confirmed end
LLM_TTFT_MS = 150         # fast small model first token
LLM_MS_PER_TOKEN = 12     # streaming decode
TTS_FIRST_MS = 80         # flash-class TTS first audio (Cartesia/Inworld Flash)
TTS_MS_PER_CHAR = 2       # synthesis keeps up with playback
WORDS_PER_CHUNK = 4       # partial granularity


@dataclass
class STTResult:
    partials: list[str]
    final: str
    simulated_ms: int = STT_PARTIAL_MS


class FakeSTT:
    """Scripted caller audio: full text in, partials + final out."""

    def transcribe(self, full_text: str) -> STTResult:
        words = full_text.split()
        partials = [" ".join(words[:i])
                    for i in range(WORDS_PER_CHUNK, len(words), WORDS_PER_CHUNK)]
        return STTResult(partials=partials, final=full_text)


@dataclass
class LLMResult:
    tokens: list[str]
    answer: str
    tool_calls: list[dict] = field(default_factory=list)
    simulated_ttft_ms: int = LLM_TTFT_MS


class FakeLLM:
    """Kernel-backed 'LLM': runs REAL graph search + triage + draft, then
    streams the draft as tokens. Decisions are production code paths."""

    def __init__(self, graph, intake_fn):
        self.graph = graph
        self.intake_fn = intake_fn

    def respond(self, transcript: str, meta: dict) -> LLMResult:
        context, evidence = self.graph.context(transcript)
        call = self.intake_fn(transcript, meta)
        answer = call["draft_response"]
        tools = [{"name": "triage_urgency", "result": call["level"]}]
        if call.get("proposed_slots"):
            tools.append({"name": "offer_slots", "result": call["proposed_slots"][0]})
        return LLMResult(tokens=answer.split(), answer=answer, tool_calls=tools)


@dataclass
class TTSChunk:
    text: str
    audio_bytes: int  # fake payload size; timing is what matters
    simulated_ms: int


class FakeTTS:
    """Clause-streaming TTS: first chunk fast, rest stream behind playback."""

    def synthesize(self, text: str) -> list[TTSChunk]:
        import re
        clauses = [c.strip() for c in re.split(r"(?<=[,.])\s+", text) if c.strip()]
        out = []
        for i, cl in enumerate(clauses):
            first = (i == 0)
            out.append(TTSChunk(text=cl, audio_bytes=len(cl) * 32,
                                simulated_ms=TTS_FIRST_MS if first
                                else len(cl) * TTS_MS_PER_CHAR))
        return out
