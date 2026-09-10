"""VoltLine voice agent on LiveKit-on-Telnyx. The mouth; the kernel decides.

Call path: Telnyx DID -> SIP -> LiveKit room -> this worker -> kernel HTTP API.
Every fact comes from the kernel (/calls/intake, /funnel/book); this process holds
NO prices, NO policies, NO booking state. Guard + audit live server-side.

Setup: see README.md in this folder. Needs Telnyx DID + TELNYX_API_KEY; no other
infra (no third-party SIP fees — Telnyx is the carrier).
"""
from __future__ import annotations
import os

KERNEL_BASE_URL = os.getenv("KERNEL_BASE_URL", "http://127.0.0.1:8080")
KERNEL_KEY = os.getenv("SPARKY_API_KEYS", "").split(",")[0].strip()


def _post(path: str, payload: dict) -> dict:
    import httpx
    r = httpx.post(KERNEL_BASE_URL.rstrip("/") + path, json=payload,
                   headers={"X-VoltLine-Key": KERNEL_KEY} if KERNEL_KEY else {},
                   timeout=20)
    r.raise_for_status()
    return r.json()


async def entrypoint(ctx):
    """LiveKit job entry. Imports are local so plain `python -m py_compile`
    and unit tests never need livekit installed."""
    from livekit.agents import Agent, AgentSession, JobContext, function_tool
    from livekit.plugins import openai, silero, telnyx
    from .prompts import system_instructions
    from app.tradie import load_profile

    profile = load_profile(os.getenv("TRADIE_PROFILE", "knowledge/tradie_profile.yaml"))

    @function_tool
    async def triage_urgency(transcript: str, caller: str = "",
                             postcode: str = "") -> str:
        """Decide wake-now vs morning ticket for a caller turn. Call FIRST."""
        import datetime
        res = _post("/calls/intake", {
            "transcript": transcript, "phone": caller, "postcode": postcode,
            "channel": "voice", "hour": datetime.datetime.now().hour,
            "day": datetime.datetime.now().strftime("%Y-%m-%d")})
        return (f"level={res['level']} reason={res['reason']} "
                f"draft={res['draft_response']} slots={res['proposed_slots']}")

    @function_tool
    async def book_survey(name: str, phone: str, postcode: str,
                          slot: str = "next-available") -> str:
        """Book a survey slot. Idempotent — pass one key per caller ever."""
        import uuid
        res = _post("/funnel/book", {
            "name": name, "phone": phone, "postcode": postcode, "slot": slot,
            "idempotency_key": f"voice-{uuid.uuid4().hex[:12]}"})
        return f"booked {res.get('booking_id')} case {res.get('case_id')}"

    session = AgentSession(
        stt=telnyx.STT(),
        llm=openai.LLM.with_telnyx(model=os.getenv("VOICE_LLM", "kimi")),
        tts=telnyx.TTS(voice=os.getenv("VOICE_TTS", "Telnyx.Ultra.Clara")),
        vad=silero.VAD.load(),
    )
    agent = Agent(instructions=system_instructions(profile),
                  tools=[triage_urgency, book_survey])
    await ctx.connect()
    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    from livekit.agents import cli, WorkerOptions
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
