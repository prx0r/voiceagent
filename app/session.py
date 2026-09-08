"""Realtime session bus (LiveKit) + HTTP fallback.

Transport interface: the conversation logic never knows which one is
live. HTTP /chat keeps working exactly as before; LiveKit rooms carry
voice/data when a server is configured. SIP/Telnyx attaches later at
the LiveKit layer, not here.
"""
from __future__ import annotations
import os


def configured() -> bool:
    return bool(os.getenv("LIVEKIT_URL") and os.getenv("LIVEKIT_API_KEY")
                and os.getenv("LIVEKIT_API_SECRET"))


def room_name(case_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-"
                   for c in str(case_id or "lobby"))[:48].strip("-") or "lobby"
    return f"support-{safe}"


def mint_token(identity: str, room: str, role: str = "caller") -> dict:
    """caller: mic+camera+data. agent: mic+data. observer: silent."""
    if not configured():
        raise RuntimeError("livekit not configured")
    sources = {"caller": ["MICROPHONE", "CAMERA"],
               "agent": ["MICROPHONE"],
               "observer": []}.get(role)
    if sources is None:
        raise ValueError(f"unknown role: {role}")
    from datetime import timedelta
    from livekit import api
    token = (api.AccessToken(os.getenv("LIVEKIT_API_KEY"),
                             os.getenv("LIVEKIT_API_SECRET"))
             .with_identity(str(identity)[:64])
             .with_name(str(identity)[:64])
             .with_grants(api.VideoGrants(
                 room_join=True, room=room,
                 can_publish=bool(sources),
                 can_publish_sources=sources or None,
                 can_publish_data=True, can_subscribe=True))
             .with_ttl(timedelta(seconds=3600)))
    return {"token": token.to_jwt(), "url": os.getenv("LIVEKIT_URL"),
            "room": room, "identity": identity, "role": role}


async def ensure_room(room: str) -> dict:
    if not configured():
        return {"ok": False, "error": "livekit not configured"}
    from livekit import api
    try:
        async with api.LiveKitAPI(
                os.getenv("LIVEKIT_URL"), os.getenv("LIVEKIT_API_KEY"),
                os.getenv("LIVEKIT_API_SECRET")) as lk:
            await lk.room.create_room(api.CreateRoomRequest(name=room))
        return {"ok": True, "room": room, "created": True}
    except Exception as e:
        if "already exists" in str(e).lower():
            return {"ok": True, "room": room, "created": False}
        return {"ok": False, "error": str(e)[:160]}
