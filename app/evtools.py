"""EV trade tools: what ChatGPT CANNOT do for a sparky.

ChatGPT already does: photo diagnosis chat, generic advice, draft quotes,
explain regs in plain English. Do NOT rebuild that.

This module does the operational stuff that needs business state:
  1. qualify_lead — score + missing-info list from 3 photos + postcode
  2. triage_urgency — after-hours wake/wait decision (the retention wedge)
  3. book_survey — slot request with idempotency (same receipt on retry)

All pure + testable, no network. Wire into ToolRegistry.descriptions().
"""
from __future__ import annotations
import re
import time
import uuid

BOOKINGS: dict[str, dict] = {}  # idempotency_key -> receipt


def qualify_lead(payload: dict) -> dict:
    """Score a domestic EV lead 0-100 + list what's missing.

    payload: {postcode?, parking_photo?, consumer_unit_photo?,
              meter_photo?, charger_shortlist?, three_phase?}
    """
    p = payload or {}
    score = 0
    missing: list[str] = []
    if p.get("postcode"):
        score += 20
    else:
        missing.append("postcode")
    if p.get("parking_photo"):
        score += 20
    else:
        missing.append("parking photo (off-street + cable route)")
    if p.get("consumer_unit_photo"):
        score += 25
    else:
        missing.append("consumer unit photo (lid open, spare ways visible)")
    if p.get("meter_photo"):
        score += 25
    else:
        missing.append("meter + main fuse photo")
    if p.get("charger_shortlist"):
        score += 10
    else:
        missing.append("charger shortlist (Ohme/Easee/Pod Point/Tesla/zappi)")

    three_phase = bool(p.get("three_phase"))
    ready = score >= 80 and not three_phase
    # three-phase always needs human survey regardless of photos
    next_step = (
        "book remote survey slot" if ready
        else "engineer review (three-phase/DNO path)" if three_phase
        else f"ask customer for: {', '.join(missing)}"
    )
    return {"ok": True, "tier": "safe", "score": score,
            "ready_to_book": ready, "missing": missing,
            "next": next_step}


URGENT_RE = re.compile(
    r"burning|smoke|shock|spark|hot|melt|smell.*burn|fire|exposed.?wire"
    r"|buzzing|crackling|arcing|sizzling",
    re.I)
NOT_CHARGING_RE = re.compile(
    r"not charg|won't charge|wont charge|tripp|no power|dead|stopped", re.I)

# Negation guard: "nothing hot" / "no burning smell" must not read as danger.
# A safety hit only counts if NOT negated within the 3 preceding words. Mixed
# (one denied, one asserted) still wakes — fail-closed toward safety.
NEG_RE = re.compile(r"\b(no|not|nothing|without|never|n't|isnt|arent)\b", re.I)


def _asserted_safety(m: str) -> bool:
    hits = list(URGENT_RE.finditer(m or ""))
    if not hits:
        return False
    for h in hits:
        window = (m or "").lower()[:h.start()].split()[-3:]
        if not any(NEG_RE.fullmatch(w.strip(".,")) for w in window):
            return True
    return False


def triage_urgency(message: str, hour: int | None = None,
                   vulnerable: bool = False) -> dict:
    """After-hours decision: WAKE engineer now vs next-working-day ticket.

    Returns {level: wake_now|same_day|routine, reason}.
    Conservative by design: any safety signal => wake_now.
    """
    m = message or ""
    if _asserted_safety(m):
        return {"ok": True, "tier": "safe", "level": "wake_now",
                "reason": "safety signal — power off if safe, engineer now"}
    if NOT_CHARGING_RE.search(m) and vulnerable:
        return {"ok": True, "tier": "safe", "level": "wake_now",
                "reason": "total loss of charge + vulnerable customer"}
    h = hour if hour is not None else time.localtime().tm_hour
    out_of_hours = h < 8 or h >= 18
    if NOT_CHARGING_RE.search(m):
        return {"ok": True, "tier": "safe",
                "level": "same_day" if not out_of_hours else "routine",
                "reason": "fault without safety signal — "
                          + ("same-day ticket" if not out_of_hours
                             else "next-working-day ticket, no wake")}
    return {"ok": True, "tier": "safe", "level": "routine",
            "reason": "general enquiry — survey/callback path"}


def book_survey(args: dict) -> dict:
    """Book a remote survey slot. Idempotent on idempotency_key."""
    key = str(args.get("idempotency_key", "") or "")
    if key and key in BOOKINGS:
        old = dict(BOOKINGS[key])
        old["replayed"] = True
        return old
    name = str(args.get("name", "") or "").strip()
    phone = str(args.get("phone", "") or "").strip()
    postcode = str(args.get("postcode", "") or "").strip()
    if not (name and phone and postcode):
        return {"ok": False, "error": "name, phone, postcode required"}
    receipt = {"ok": True, "tier": "moderate",
               "booking_id": f"SURV-{uuid.uuid4().hex[:6].upper()}",
               "slot": str(args.get("slot", "next-available")),
               "name": name, "phone": phone, "postcode": postcode,
               "idempotency_key": key}
    if key:
        BOOKINGS[key] = dict(receipt)
    return receipt


DESCRIPTIONS = {
    "qualify_lead": "Score an EV lead 0-100 + missing photos. args: postcode?, parking_photo?, consumer_unit_photo?, meter_photo?, charger_shortlist?, three_phase?",
    "triage_urgency": "After-hours wake/wait decision. args: message, hour?, vulnerable?",
    "book_survey": "Book free remote survey. args: name, phone, postcode, slot?, idempotency_key?",
}
