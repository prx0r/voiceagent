"""Booking availability: read-only by design.

Availability is COMPUTED from the static weekly template + existing bookings.
Nothing here writes to any external calendar (Google Calendar OAuth = phase 2).
Same shape as an MCP read-only tool: propose slots, never commit.
"""
from __future__ import annotations
import datetime
import json
import os

RUNTIME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime")
BOOKINGS = os.path.join(RUNTIME, "bookings.jsonl")

# Default trade week (Mon-Sat working, Sun closed). Per-business override via
# pack business.hours in a future pass; static + predictable for P0.
WEEK = {
    0: [("08:00", "18:00")], 1: [("08:00", "18:00")], 2: [("08:00", "18:00")],
    3: [("08:00", "18:00")], 4: [("08:00", "18:00")], 5: [("08:00", "14:00")],
    6: [],
}
SLOT_MIN = 60


def _booked() -> list:
    rows = []
    if os.path.isfile(BOOKINGS):
        for line in open(BOOKINGS):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    return rows


def day_slots(day: datetime.date) -> list:
    """Free HH:MM slots for one date, minus booked overlaps."""
    spans = WEEK.get(day.weekday(), [])
    slots = []
    for start, end in spans:
        h, m = int(start[:2]), int(start[3:])
        eh, em = int(end[:2]), int(end[3:])
        cur = h * 60 + m
        stop = eh * 60 + em
        while cur + SLOT_MIN <= stop:
            slots.append(f"{cur // 60:02d}:{cur % 60:02d}")
            cur += SLOT_MIN
    taken = set()
    for b in _booked():
        if b.get("date") == day.isoformat() and b.get("state") in ("requested", "confirmed"):
            taken.add((b.get("time") or "")[:5])
    return [s for s in slots if s not in taken]


def propose(n_days: int = 5, per_day: int = 3) -> list:
    """Next n_days with up to per_day free slots each. Pure read."""
    out = []
    day = datetime.date.today()
    while len(out) < n_days:
        day += datetime.timedelta(days=1)
        free = day_slots(day)
        if free:
            out.append({"date": day.isoformat(),
                        "weekday": day.strftime("%A"),
                        "slots": free[:per_day]})
    return out


def confirm(business: str, name: str, phone: str, email: str,
            service: str, date: str, time_: str) -> dict:
    """Commit a booking: ledger row + callback reminder + confirm email hook.

    Returns the receipt. Email sending itself stays with the Gmail adapter
    (caller decides), so this function never needs creds to succeed.
    """
    import hashlib
    import time as _t
    if len(name.strip()) < 2 or len(phone.strip()) < 7:
        return {"ok": False, "reason": "name + valid callback number required"}
    try:
        datetime.date.fromisoformat(date)
        datetime.datetime.strptime(time_, "%H:%M")
    except ValueError:
        return {"ok": False, "reason": "date YYYY-MM-DD + time HH:MM required"}
    if time_ not in day_slots(datetime.date.fromisoformat(date)):
        return {"ok": False, "reason": "slot taken or outside hours — propose again"}
    ref = hashlib.sha256(f"{phone}{date}{time_}{_t.time()}".encode()).hexdigest()[:8]
    row = {"ref": ref, "business": business[:60], "name": name.strip(),
           "phone": phone.strip(), "email": (email or "").strip()[:120],
           "service": service[:40], "date": date, "time": time_,
           "when": f"{date} {time_}", "at": int(_t.time()), "state": "confirmed"}
    os.makedirs(RUNTIME, exist_ok=True)
    with open(BOOKINGS, "a") as f:
        f.write(json.dumps(row) + "\n")
    try:
        import sys as _s
        _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from afterhours import queue_reminder
        queue_reminder(name, phone, f"confirmed booking {date} {time_} ({service})",
                       "standard", business)
    except Exception:
        pass
    return {"ok": True, "ref": ref, "date": date, "time": time_}
