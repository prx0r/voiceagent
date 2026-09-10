"""Qwen voice adapter (production voice in/out). See docs/QWEN_OMNI.md.

Design: voice is a CHANNEL, not the brain. Same kernel always:
  caller audio -> Qwen realtime (ears/mouth) -> transcript
  -> graph.context() evidence -> OUR tool call (survey/urgency/booking/calendar)
  -> guard.enforce() -> speak back.

Model choice (per current QwenCloud docs):
  - WS + guaranteed function-calling: qwen-audio-3.0-realtime-plus (default here),
    flash variant for cheap. 3.5-Omni realtime docs contradict themselves on WS
    tools, so we never depend on model-side tools alone — tools run server-side
    from transcripts regardless of model.
  - Function calling and web search are mutually exclusive on Omni: we run
    tools-mode, search off. Parts/price facts come from our tables, not the model.

Env: QWEN_API_KEY, QWEN_MODEL, QWEN_VOICE (default Tina for 3.5 / server default
otherwise), QWEN_WS_URL override for region pinning.
"""
from __future__ import annotations
import os
import uuid as _uuid

MODEL = os.getenv("QWEN_MODEL", "qwen-audio-3.0-realtime-plus")
VOICE = os.getenv("QWEN_VOICE", "Tina")
WS_URL = os.getenv("QWEN_WS_URL",
                   "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime")
API_KEY = os.getenv("QWEN_API_KEY", "")

SYSTEM_CONSTRAINT = """You are the voice renderer for VoltLine Electrical, not the decider.
Rules: quote ONLY the supplied ANSWER text. Never add prices, grants, dates,
certification claims, or new facts. If asked for anything outside the ANSWER,
say you will log it for the engineer. Two sentences max. Same language as caller."""


def session_update_event(instructions: str = "", tools: list | None = None) -> dict:
    """Build the required first WS message. Pure — unit-testable, no network."""
    return {
        "event_id": f"event_{_uuid.uuid4().hex[:16]}",
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "voice": VOICE,
            "input_audio_format": "pcm",
            "output_audio_format": "pcm",
            "instructions": instructions or SYSTEM_CONSTRAINT,
            "turn_detection": {"type": "semantic_vad", "threshold": 0.5,
                               "silence_duration_ms": 800},
            # NOTE: tools XOR enable_search. We always take tools.
            **({"tools": tools} if tools else {}),
        },
    }


def function_output_event(call_id: str, output: str) -> dict:
    return {
        "event_id": f"event_{_uuid.uuid4().hex[:16]}",
        "type": "conversation.item.create",
        "item": {"type": "function_call_output", "call_id": call_id,
                 "output": output[:2000]},
    }


async def speak_once(text: str, out_dir: str = "runtime/tts") -> str:
    """HTTP/dev fallback. No key -> edge_tts so tests and demos still talk."""
    os.makedirs(out_dir, exist_ok=True)
    if not API_KEY:
        from .edge_tts import synthesize
        return await synthesize(text, os.getenv("EDGE_TTS_VOICE", "en-GB-RyanNeural"), out_dir)
    import httpx
    base = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            base + "/services/aigc/multimodal-generation/generation",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL.replace("-realtime", ""),
                  "input": {"text": text}, "parameters": {"voice": VOICE}},
        )
        r.raise_for_status()
        data = r.json()
    path = os.path.join(out_dir, f"{_uuid.uuid4().hex}.mp3")
    audio = (data.get("output") or {}).get("audio") or {}
    if audio.get("url"):
        import httpx as _hx
        async with _hx.AsyncClient(timeout=30) as c:
            b = await c.get(audio["url"])
            open(path, "wb").write(b.content)
    else:
        import base64
        b64 = (data.get("output") or {}).get("audio_data", "")
        open(path, "wb").write(base64.b64decode(b64) if b64 else b"")
    return path


async def realtime_session(on_transcript, on_function_call, instructions: str = "",
                           tools: list | None = None):
    """Full-duplex WS. Caller owns mic/playback; kernel owns tools.

    on_transcript(text, is_final) — final ones go into graph.context()+LLM.
    on_function_call(name, args, call_id) — route via ToolRegistry, reply with
      function_output_event(result) then response.create. Never exec client-side.
    """
    try:
        import websockets  # type: ignore
    except ImportError as e:
        raise RuntimeError("pip install websockets to use Qwen realtime") from e
    if not API_KEY:
        raise RuntimeError("QWEN_API_KEY not set")
    import json
    url = f"{WS_URL}?model={MODEL}"
    async with websockets.connect(url, extra_headers={  # type: ignore
            "Authorization": f"Bearer {API_KEY}"}) as ws:
        await ws.send(json.dumps(session_update_event(instructions, tools)))
        async for raw in ws:
            msg = json.loads(raw)
            t = msg.get("type", "")
            if t == "conversation.item.input_audio_transcription.completed":
                await on_transcript(msg.get("transcript", ""), True)
            elif t == "response.function_call_arguments.done":
                await on_function_call(msg.get("name", ""),
                                       msg.get("arguments", {}),
                                       msg.get("call_id", ""))
