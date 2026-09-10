"""WhatsApp Cloud API sender. Real request shape, env-gated.

Needs (Meta Cloud API via BSP or direct): WHATSAPP_TOKEN, WHATSAPP_PHONE_ID.
Without keys: logs to var/whatsapp_out.jsonl and returns ok:queued-locally so
the MVP works end-to-end (sparky app, digest, tests) before Meta approval
(5-10 working days typical). Text + template shapes included; voice notes and
PDF certs go through the same send() with type=document/audio.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
OUT = Path("var/whatsapp_out.jsonl")


def send(to: str, text: str, kind: str = "text",
         media_url: str = "", caption: str = "") -> dict:
    payload = {"messaging_product": "whatsapp", "to": to, "type": kind}
    if kind == "text":
        payload["text"] = {"body": text[:4000], "preview_url": False}
    elif kind == "template":
        payload["template"] = {"name": media_url or "job_update",
                               "language": {"code": "en_GB"}}
    elif kind in ("document", "audio", "image"):
        payload[kind] = {"link": media_url, "caption": caption[:1000]}
    if not (TOKEN and PHONE_ID):
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "a") as f:
            f.write(json.dumps({"t": time.time(), "to": to,
                                "payload": payload}) + "\n")
        return {"ok": True, "tier": "moderate", "queued": "local",
                "note": "set WHATSAPP_TOKEN+PHONE_ID for live send"}
    import httpx
    import asyncio

    async def _post():
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                f"https://graph.facebook.com/v21.0/{PHONE_ID}/messages",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json=payload)
            r.raise_for_status()
            return r.json()
    try:
        res = asyncio.run(_post())
        return {"ok": True, "tier": "moderate", "provider_id": str(res)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


DESCRIPTIONS = {
    "whatsapp_send": "Send WhatsApp text/template/doc. args: to, text?, kind?, media_url?, caption?",
}
