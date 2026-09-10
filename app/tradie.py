"""Tradie kernel: profile-aware quotes, worth-it scoring, job stats.

Reads knowledge/tradie_profile.yaml. Pure functions so tests don't need disk
except stats log (JSONL, append-only).
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

import yaml

PROFILE_PATH = "knowledge/tradie_profile.yaml"
STATS_PATH = "runtime/job_stats.jsonl"


def load_profile(path: str = PROFILE_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def drive_min(from_postcode: str, to_postcode: str) -> int:
    """Stub distance. Same outcode ~12 min, same area-letter ~22, else 35.

    Swap for OSRM/Google Distance Matrix later — callers unchanged.
    """
    a = (from_postcode or "").strip().upper().split()[0]
    b = (to_postcode or "").strip().upper().split()[0]
    if not a or not b:
        return 20
    if a == b:
        return 12
    la, lb = re.sub(r"[^A-Z]", "", a), re.sub(r"[^A-Z]", "", b)
    if la and la == lb:
        return 22
    if la[:1] and la[:1] == lb[:1]:
        return 28
    return 35


_JOB_ALIASES = {
    "ev_charger": ["ev", "charger", "ohme", "easee", "pod point", "tesla", "zappi"],
    "consumer_unit": ["consumer unit", "fuse board", "fusebox", "board"],
    "fault_find": ["fault", "tripp", "not working", "dead", "no power"],
    "eicr": ["eicr", "condition report", "landlord cert"],
}


def job_type_of(text: str) -> str:
    m = (text or "").lower()
    for jt, keys in _JOB_ALIASES.items():
        if any(k in m for k in keys):
            return jt
    return "general"


def worth_it(profile: dict, job: dict) -> dict:
    """Score 0-100 from money/ease/enjoy/distance/calendar-fit. With reasons."""
    prefs = (profile.get("preferences") or {})
    prices = (profile.get("prices") or {})
    mins = drive_min((profile.get("tradie") or {}).get("base_postcode", ""),
                     job.get("postcode", ""))
    maxd = int(prefs.get("max_drive_min", 35))
    jt = job_type_of(job.get("summary", "") + " " + job.get("charger", ""))
    enjoys = prefs.get("enjoys", []) or []
    dislikes = prefs.get("dislikes", []) or []

    score = 50
    reasons = []
    value = float(job.get("value_gbp", 300) or 300)
    if value >= 800:
        score += 20; reasons.append(f"good value £{value:g}")
    elif value < 150:
        score -= 15; reasons.append(f"low value £{value:g}")
    if mins <= 15:
        score += 15; reasons.append(f"{mins} min away")
    elif mins > maxd:
        score -= 25; reasons.append(f"{mins} min drive (over {maxd} max)")
    else:
        score += 0; reasons.append(f"{mins} min drive")
    if jt in enjoys:
        score += 10; reasons.append(f"you like {jt}")
    if any(d.split("_")[0] in jt or jt in d for d in dislikes):
        score -= 10; reasons.append(f"not your favourite ({jt})")
    ease = str(job.get("ease", "medium")).lower()
    if ease == "easy":
        score += 5
    elif ease == "hard":
        score -= 10; reasons.append("looks hard from photos")
    if job.get("slot_is_morning") and prefs.get("mornings_first"):
        score += 5; reasons.append("morning slot")
    score = max(0, min(100, score))
    verdict = "take it" if score >= 65 else "maybe" if score >= 40 else "skip/pass on"
    # stat-aware nudge: if this type usually overruns, say so
    avg = avg_duration(jt)
    if avg and avg > 180:
        reasons.append(f"note: your {jt} avg is {avg:.0f} min")
    return {"score": score, "verdict": verdict, "reasons": reasons,
            "job_type": jt, "drive_min": mins}


def draft_quote(profile: dict, job: dict, parts_total: float = 0) -> dict:
    """Pre-draft customer reply + price range. Ranges only, validity stamped."""
    prices = profile.get("prices") or {}
    q = profile.get("quotes") or {}
    msgs = profile.get("messages") or {}
    jt = job_type_of(job.get("summary", "") + " " + job.get("charger", ""))
    lo = hi = None
    if jt == "ev_charger":
        lo, hi = (prices.get("ev_7kw_standard") or [950, 1400])[:2]
    elif jt == "consumer_unit":
        lo, hi = (prices.get("consumer_unit_10way") or [550, 850])[:2]
    elif jt == "eicr":
        lo, hi = (prices.get("eicr_2bed") or [160, 240])[:2]
    else:
        h = float(prices.get("hourly", 65))
        lo, hi = h, h * 2
    if parts_total:
        lo, hi = round(lo + parts_total, 2), round(hi + parts_total, 2)
    slots = job.get("proposed_slots") or []
    slot_txt = f"I'm free {slots[0]}" if slots else "I can offer times tomorrow"
    text = (f"Hi {job.get('name','there')} — {slot_txt}. "
            f"Rough range £{lo:g}–£{hi:g} incl cert, valid {q.get('validity_days',14)} days, "
            f"final after survey. {msgs.get('signoff','')}".strip())
    return {"ok": True, "text": text, "range": [lo, hi],
            "validity_days": q.get("validity_days", 14)}


def log_job_time(job_type: str, minutes: float, case_id: str = "",
                 path: str = STATS_PATH) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps({"t": time.time(), "job_type": job_type,
                            "minutes": minutes, "case": case_id}) + "\n")
    return {"ok": True}


def avg_duration(job_type: str, path: str = STATS_PATH) -> float | None:
    p = Path(path)
    if not p.exists():
        return None
    vals = []
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
            if r.get("job_type") == job_type:
                vals.append(float(r.get("minutes", 0)))
        except Exception:
            continue
    return sum(vals) / len(vals) if vals else None
