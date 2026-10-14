"""After-hours flow: missed call -> urgency -> SMS owner -> email digest -> reminders.

No creds -> every send degrades to a queued intent (JSONL outbox), never a
silent drop and never an exception. Wire Telnyx/Gmail keys when ready.
"""
from __future__ import annotations
import json
import os
import time
import urllib.request

RUNTIME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime")
OUTBOX = os.path.join(RUNTIME, "outbox.jsonl")
REMINDERS = os.path.join(RUNTIME, "reminders.jsonl")
CALLS_LEDGER = os.path.join(RUNTIME, "calls.jsonl")
RATE_PER_MIN_GBP = float(os.getenv("RATE_PER_MIN_GBP", "0.50"))

EMERGENCY_WORDS = ("burst", "flood", "sewage", "no water", "gas smell",
                   "no heating", "no hot water", "carbon monoxide",
                   "spark", "burning", "smoke", "exposed wire",
                   "exposed wires", "power cut", "no power", "fuse box",
                   "elderly", "vulnerable", "baby", "disabled")
REMIND_EVERY_SECS = int(os.getenv("REMIND_EVERY_SECS", "7200"))  # 2h


def classify_urgency(issue: str) -> str:
    text = (issue or "").lower()
    return "emergency" if any(w in text for w in EMERGENCY_WORDS) else "standard"


def _append(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if "business" not in row:
        row["business"] = os.getenv("BUSINESS_SLUG", "default")
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def sms_owner(to: str, body: str) -> dict:
    """Instant SMS via Telnyx when TELNYX_API_KEY is set, else queued intent."""
    key = os.getenv("TELNYX_API_KEY", "").strip()
    sender = os.getenv("TELNYX_FROM", "").strip()
    if not key or not sender or not to:
        _append(OUTBOX, {"at": int(time.time()), "kind": "sms",
                         "to": to, "body": body[:300], "state": "queued-no-creds"})
        return {"ok": False, "queued": True,
                "next": "set TELNYX_API_KEY + TELNYX_FROM to send live"}
    try:
        req = urllib.request.Request(
            "https://api.telnyx.com/v2/messages",
            data=json.dumps({"from": sender, "to": to, "text": body[:1600]}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read() or b"{}")
        _append(OUTBOX, {"at": int(time.time()), "kind": "sms",
                         "to": to, "state": "sent",
                         "id": str(resp.get("data", {}).get("id", ""))})
        return {"ok": True}
    except Exception as e:
        _append(OUTBOX, {"at": int(time.time()), "kind": "sms",
                         "to": to, "body": body[:300],
                         "state": f"failed: {e}"[:160]})
        return {"ok": False, "queued": True, "reason": str(e)[:120]}


def whatsapp_ping(to: str, body: str) -> dict:
    """WhatsApp ping via Meta API when WHATSAPP_TOKEN + WHATSAPP_PHONE_ID
    are set, else queued intent. Same degrade pattern as SMS."""
    token = os.getenv("WHATSAPP_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_ID", "").strip()
    if not token or not phone_id or not to:
        _append(OUTBOX, {"at": int(time.time()), "kind": "whatsapp",
                         "to": to, "body": body[:300], "state": "queued-no-creds"})
        return {"ok": False, "queued": True,
                "next": "set WHATSAPP_TOKEN + WHATSAPP_PHONE_ID to send live"}
    try:
        req = urllib.request.Request(
            f"https://graph.facebook.com/v22.0/{phone_id}/messages",
            data=json.dumps({"messaging_product": "whatsapp", "to": to,
                             "type": "text", "text": {"body": body[:4000]}}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read() or b"{}")
        _append(OUTBOX, {"at": int(time.time()), "kind": "whatsapp",
                         "to": to, "state": "sent",
                         "id": str(resp.get("messages", [{}])[0].get("id", ""))})
        return {"ok": True}
    except Exception as e:
        _append(OUTBOX, {"at": int(time.time()), "kind": "whatsapp",
                         "to": to, "body": body[:300],
                         "state": f"failed: {e}"[:160]})
        return {"ok": False, "queued": True, "reason": str(e)[:120]}


def format_whatsapp(call: dict) -> str:
    return (f"🔌 {call.get('business', 'Your sparky')} missed call\n"
            f"Who: {call.get('caller', '?')} {call.get('number', '?')}\n"
            f"Why: {call.get('issue', '?')[:160]}\n"
            f"Ring back: {'NOW - emergency' if call.get('urgency') == 'emergency' else 'next working morning'}\n"
            f"@{call.get('address', '?')}"[:900])


def log_call(business: str, caller: str, started_ts: int, ended_ts: int) -> dict:
    """Per-minute ledger. 50p/min active by default (RATE_PER_MIN_GBP)."""
    import math
    secs = max(0, int(ended_ts) - int(started_ts))
    mins = math.ceil(secs / 60)
    amount = round(mins * RATE_PER_MIN_GBP, 2)
    row = {"business": business, "caller": caller, "started": int(started_ts),
           "ended": int(ended_ts), "secs": secs, "mins": mins,
           "rate_gbp_min": RATE_PER_MIN_GBP, "amount_gbp": amount}
    _append(CALLS_LEDGER, row)
    return {"ok": True, **row}


def ledger_totals(business: str = "") -> dict:
    total_mins, total_gbp, n = 0, 0.0, 0
    if os.path.isfile(CALLS_LEDGER):
        for line in open(CALLS_LEDGER):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if business and r.get("business") != business:
                continue
            n += 1
            total_mins += r.get("mins", 0)
            total_gbp += r.get("amount_gbp", 0.0)
    return {"calls": n, "mins": total_mins, "gbp": round(total_gbp, 2)}


def queue_reminder(caller: str, number: str, issue: str, urgency: str,
                   business: str = "") -> dict:
    row = {"business": business or os.getenv("BUSINESS_SLUG", "default"),
           "caller": caller, "number": number, "issue": issue[:500],
           "urgency": urgency, "created": int(time.time()),
           "next_due": int(time.time()) + REMIND_EVERY_SECS,
           "nags": 0, "done": False}
    _append(REMINDERS, row)
    return {"ok": True, "next_due_in_secs": REMIND_EVERY_SECS}


def handle_missed_call(caller: str, number: str, issue: str, address: str,
                       owner_mobile: str, digest_to: str,
                       backup_contact: str = "", whatsapp_to: str = "",
                       business: str = "") -> dict:
    """Full after-hours intake. Returns what happened + what is queued."""
    from adapters.gmail_notify import send_digest, format_call_note
    urgency = classify_urgency(issue)
    call = {"business": business or "Your sparky", "caller": caller,
            "number": number, "issue": issue,
            "address": address, "urgency": urgency,
            "at": time.strftime("%Y-%m-%d %H:%M"),
            "recommendation": ("attend tonight, owner called back within the hour"
                               if urgency == "emergency"
                               else "callback next working morning")}
    outcome = {"urgency": urgency, "sms": None, "whatsapp": None,
               "email": None, "reminder": None}
    if urgency == "emergency":
        outcome["sms"] = sms_owner(
            owner_mobile,
            f"EMERGENCY {call['at']} {caller} {number}: {issue[:120]} @ {address[:80]}")
        if backup_contact and not outcome["sms"].get("ok"):
            outcome["sms_backup"] = sms_owner(
                backup_contact, f"BACKUP EMERGENCY {caller} {number}: {issue[:120]}")
    if whatsapp_to:
        outcome["whatsapp"] = whatsapp_ping(whatsapp_to, format_whatsapp(call))
    outcome["email"] = send_digest(
        digest_to, f"[after-hours {urgency}] {caller} - {issue[:60]}",
        format_call_note(call))
    outcome["reminder"] = queue_reminder(caller, number, issue, urgency,
                                       business or os.getenv("BUSINESS_SLUG", "default"))
    return outcome
