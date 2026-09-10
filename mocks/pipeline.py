"""Minimal frame pipeline mirroring Pipecat semantics (no dependency).

Stages: transport -> STT -> speculative aggregator -> LLM -> TTS -> transport.
- Eager partials trigger SPECULATIVE LLM runs (Prefetch on partials).
- Confirmed end either keeps the run (match) or rolls back + re-runs (mismatch).
- Barge-in: caller text injected mid-response cancels remaining TTS chunks and
  starts a new turn; audit records what was spoken vs dropped (Deepgram v2/speak
  Interrupt semantics: text_spoken vs text_remaining).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .providers import (FakeSTT, FakeLLM, FakeTTS, ENDPOINT_MS, EAGER_MS,
                        LLM_MS_PER_TOKEN)


@dataclass
class TurnReport:
    caller_text: str
    final_text: str
    answer: str
    tool_calls: list[dict]
    evidence: list[str] = field(default_factory=list)
    speculated: bool = False
    speculation_kept: bool = False
    barged_in: bool = False
    text_spoken: str = ""
    text_dropped: str = ""
    simulated_ms: int = 0  # caller-stops to first-audio, model-based


class VoiceLoop:
    def __init__(self, graph, intake_fn, stt=None, llm=None, tts=None):
        self.stt = stt or FakeSTT()
        self.llm = llm or FakeLLM(graph, intake_fn)
        self.tts = tts or FakeTTS()
        self.graph = graph
        self.audit: list[dict] = []

    def _latency(self, answer: str, spec_kept: bool) -> int:
        from .providers import TTS_FIRST_MS, LLM_TTFT_MS
        first_clause = answer.split(",")[0].split(".")[0]
        gen_ms = len(first_clause.split()) * LLM_MS_PER_TOKEN
        base = ENDPOINT_MS + TTS_FIRST_MS + min(LLM_TTFT_MS, gen_ms)
        if spec_kept:
            base -= (ENDPOINT_MS - EAGER_MS)  # prefill hid inside endpointing
        return max(base, TTS_FIRST_MS + 20)

    def turn(self, caller_text: str, meta: dict,
             barge_in: str | None = None,
             barge_at_chars: int = 60) -> TurnReport:
        stt = self.stt.transcribe(caller_text)
        # Speculative run on last eager partial (if any and non-trivial).
        spec = None
        if stt.partials and len(stt.partials[-1].split()) > 3:
            spec = self.llm.respond(stt.partials[-1], meta)
        final = self.llm.respond(stt.final, meta)
        kept = bool(spec and stt.final.startswith(stt.partials[-1][:20]))
        _, evidence = self.graph.context(stt.final)
        chunks = self.tts.synthesize(final.answer)

        rep = TurnReport(
            caller_text=caller_text, final_text=stt.final,
            answer=final.answer, tool_calls=final.tool_calls,
            evidence=[e["id"] for e in evidence],
            speculated=spec is not None, speculation_kept=kept,
            simulated_ms=self._latency(final.answer, kept))

        if barge_in:
            spoken, dropped, n = [], [], 0
            for ch in chunks:
                if n + len(ch.text) <= barge_at_chars:
                    spoken.append(ch.text)
                    n += len(ch.text)
                else:
                    dropped.append(ch.text)
            rep.barged_in = True
            rep.text_spoken = " ".join(spoken)
            rep.text_dropped = " ".join(dropped)
            # New turn from the interruption (context preserved, like production).
            follow = self.turn(barge_in, meta)
            self.audit.append({"event": "barge-in", "spoken": rep.text_spoken,
                               "dropped": rep.text_dropped,
                               "follow_tools": [t["name"] for t in follow.tool_calls]})
            rep.answer += f" [interrupted -> handled: {follow.answer[:80]}]"
        self.audit.append({"event": "turn", "level": final.tool_calls[0]["result"]
                           if final.tool_calls else "?", "kept_spec": kept,
                           "ms": rep.simulated_ms})
        return rep
