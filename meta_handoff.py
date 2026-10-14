"""Meta handoff receiver: handed-off WhatsApp chats -> afterhours flow.

Meta posts messaging_handovers to our webhook when its agent escalates.
We turn each handoff into the same intake the phone flow produces:
reminder queued + digest note. Thread stays with the human side until
we release it (release = separate Meta call, done at case close).
"""
from __future__ import annotations
import time


def handle_handover(payload: dict, digest_to: str = "") -> dict:
    """payload: Meta messaging_handovers webhook (or our fixture shape).
    Returns receipt; never raises on malformed input."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from afterhours import queue_reminder
        from adapters.gmail_notify import send_digest
    except ImportError as e:
        return {"ok": False, "reason": f"unavailable: {e}"[:120]}
    try:
        customer = str(payload.get("customer_phone") or payload.get("to") or "?")
        metadata = str(payload.get("metadata") or "")
        text = str(payload.get("summary") or metadata or "Meta handoff")[:500]
        rem = queue_reminder(customer, customer, f"WhatsApp handoff: {text}",
                             "standard")
        note = (f"Meta Business Agent handed off a WhatsApp chat.\n"
                f"Customer: {customer}\nNote: {text}\n"
                f"Thread held on our side until released.")
        mail = send_digest(digest_to, f"[whatsapp handoff] {customer}", note) \
            if digest_to else {"ok": False, "reason": "no digest address"}
        return {"ok": True, "at": int(time.time()), "customer": customer,
                "reminder": rem.get("ok", False), "email": mail.get("ok", False)}
    except Exception as e:
        return {"ok": False, "reason": str(e)[:160]}
