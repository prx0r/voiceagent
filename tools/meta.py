"""Meta pages + email stubs. Same pattern as whatsapp: env-gated, local-log fallback.

- IG/FB: set META_PAGE_TOKEN + META_PAGE_ID (+ IG_ID for Instagram). setup_pack()
  returns the checklist to create the business pages (bio, services, WhatsApp
  link button) — the agent drafts copy, human clicks publish (least-risk path).
- Email: set SMTP_* or RESEND_API_KEY for live; else local log.
These run from /sparky/act one-click actions, never auto-sent without approval
except the overnight ACK ("got it, Dan replies in the morning").
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

OUT = Path("var/comms_out.jsonl")


def _log(channel: str, payload: dict) -> dict:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a") as f:
        f.write(json.dumps({"t": time.time(), "channel": channel,
                            "payload": payload}) + "\n")
    return {"ok": True, "tier": "moderate", "queued": "local",
            "note": "set live keys for real send"}


def page_post(text: str, image_url: str = "", network: str = "facebook") -> dict:
    tok, pid = os.getenv("META_PAGE_TOKEN", ""), os.getenv("META_PAGE_ID", "")
    if not (tok and pid):
        return _log(network, {"text": text[:1000], "image": image_url})
    return _log(network, {"text": text[:200], "live_attempt": True,
                          "note": "wire Graph API publish here"})


def send_email(to: str, subject: str, body: str) -> dict:
    if not (os.getenv("SMTP_HOST") or os.getenv("RESEND_API_KEY")):
        return _log("email", {"to": to, "subject": subject,
                              "body": body[:2000]})
    return _log("email", {"to": to, "subject": subject, "live_attempt": True})


def business_setup_pack(profile: dict) -> dict:
    t = (profile.get("tradie") or {})
    prices = (profile.get("prices") or {})
    return {"ok": True, "checklist": [
        f"FB page: {t.get('business')} — services: EV chargers, boards, EICR, faults",
        f"IG bio: {t.get('business')} ⚡ EV chargers + boards | {t.get('base_postcode','')} | WhatsApp to book",
        "FB action button -> WhatsApp chat link",
        f"Pinned post: 7kW installs £{prices.get('ev_7kw_standard',[950,1400])[0]:g}+, free remote survey, cert incl.",
        "Email footer: scheme + cert + review link",
    ]}
