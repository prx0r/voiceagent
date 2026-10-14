"""Gmail notify adapter: morning digests + call notes from our own account.

The agent sends from an address WE own (e.g. xyz.aionboard@gmail.com) via
SMTP + App Password. Clients give us nothing but a destination address.
No creds configured -> {"ok": False} with next step, never an exception.
"""
from __future__ import annotations
import os
import smtplib
from email.message import EmailMessage


def _conf() -> tuple[str, str]:
    return (os.getenv("GMAIL_USER", "").strip(),
            os.getenv("GMAIL_APP_PASS", "").strip())


def send_digest(to: str, subject: str, body: str) -> dict:
    user, pw = _conf()
    if not user or not pw:
        return {"ok": False, "reason": "gmail not configured",
                "next": "set GMAIL_USER + GMAIL_APP_PASS (App Password, 2FA on)"}
    if not to or "@" not in to:
        return {"ok": False, "reason": "destination address required"}
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = subject[:120]
    msg.set_content(body[:20000])
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(user, pw)
            s.send_message(msg)
    except Exception as e:
        return {"ok": False, "reason": f"smtp failed: {e}"[:160]}
    return {"ok": True, "to": to}


def format_call_note(call: dict) -> str:
    lines = [
        f"Call from {call.get('caller', '?')} ({call.get('number', '?')})",
        f"Time: {call.get('at', '?')}  Urgency: {call.get('urgency', 'standard')}",
        "",
        f"Issue: {call.get('issue', '?')}",
        f"Address: {call.get('address', '?')}",
        "",
        f"Recommended: {call.get('recommendation', 'callback next working morning')}",
    ]
    return "\n".join(lines)
