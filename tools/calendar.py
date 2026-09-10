"""Local calendar. JSON-file today, Google/Jobber/Tradify tomorrow.

File shape: {"events": [{"id","title","start":"2026-09-11T08:00","end":...,
"postcode":"E2 8AA","type":"ev_install|survey|fault|personal"}]}
All naive-local ISO. No deps.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_FMT = "%Y-%m-%dT%H:%M"


def _load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"events": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"events": []}


def _save(path: str, data: dict):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1))


def list_events(path: str, day: str | None = None) -> list[dict]:
    d = _load(path)["events"]
    if day:
        d = [e for e in d if str(e.get("start", "")).startswith(day)]
    return sorted(d, key=lambda e: e.get("start", ""))


def _busy(path: str) -> list[tuple[datetime, datetime]]:
    out = []
    for e in _load(path)["events"]:
        try:
            out.append((datetime.strptime(e["start"][:16], _FMT),
                        datetime.strptime(e["end"][:16], _FMT)))
        except Exception:
            continue
    return out


def free_slots(path: str, day: str, mornings_first: bool = True,
               slot_min: int = 60, buffer_min: int = 30,
               work_start: int = 8, work_end: int = 17) -> list[str]:
    """Day like '2026-09-11'. Returns ISO start times fitting slot+buffer."""
    busy = _busy(path)
    cur = datetime.strptime(day, "%Y-%m-%d").replace(hour=work_start)
    end = datetime.strptime(day, "%Y-%m-%d").replace(hour=work_end)
    step = timedelta(minutes=30)
    need = timedelta(minutes=slot_min + buffer_min)
    slots: list[str] = []
    while cur + need <= end + timedelta(seconds=1):
        s, e = cur, cur + timedelta(minutes=slot_min)
        if not any(s < b_end and e > b_start for b_start, b_end in busy):
            slots.append(s.strftime(_FMT))
        cur += step
    if mornings_first:
        slots.sort(key=lambda s: (int(s[11:13]) >= 12, s))
    return slots[:6]


def book(path: str, title: str, start: str, minutes: int,
         postcode: str = "", etype: str = "job") -> dict:
    s = datetime.strptime(start[:16], _FMT)
    e = s + timedelta(minutes=minutes)
    for b_s, b_e in _busy(path):
        if s < b_e and e > b_s:
            return {"ok": False, "error": "clashes with existing event"}
    ev = {"id": f"ev_{uuid.uuid4().hex[:6]}", "title": title,
          "start": s.strftime(_FMT), "end": e.strftime(_FMT),
          "postcode": postcode, "type": etype}
    d = _load(path)
    d["events"].append(ev)
    _save(path, d)
    return {"ok": True, "event": ev}
