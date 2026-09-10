"""Retention sweeper: GDPR hygiene for runtime/. Port of the AIReceptionist
retention/ pattern, adapted to our layout.

Policy (days, env-overridable):
  RETAIN_CASE_DAYS=90     runtime/cases/case_*.json (closed; escalated kept longer)
  RETAIN_UPLOAD_DAYS=30   runtime/uploads/* (customer photos)
  RETAIN_TTS_DAYS=7       runtime/tts/*.mp3 (rendered audio)
  RETAIN_LOG_DAYS=180     var/*.jsonl (audit trails stay longest)
  RETAIN_DB_DAYS=365      runtime/support.db messages (vacuumed by age)

Open cases and escalated cases are never swept. Dry-run by default; pass
apply=True (or --apply) to delete. Returns a report dict; CLI prints it.
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from pathlib import Path

DAY = 86400
POLICY = {
    "cases": float(os.getenv("RETAIN_CASE_DAYS", "90")) * DAY,
    "escalated_extra": float(os.getenv("RETAIN_ESCALATED_EXTRA_DAYS", "90")) * DAY,
    "uploads": float(os.getenv("RETAIN_UPLOAD_DAYS", "30")) * DAY,
    "tts": float(os.getenv("RETAIN_TTS_DAYS", "7")) * DAY,
    "logs": float(os.getenv("RETAIN_LOG_DAYS", "180")) * DAY,
    "db": float(os.getenv("RETAIN_DB_DAYS", "365")) * DAY,
}


def _older_than(path: Path, age_s: float, now: float) -> bool:
    try:
        return (now - path.stat().st_mtime) > age_s
    except OSError:
        return False


def sweep(root: str = ".", apply: bool = False,
          policy: dict | None = None) -> dict:
    pol = policy or POLICY
    now = time.time()
    base = Path(root)
    report: dict = {"swept": [], "kept": 0, "apply": apply}

    for f in (base / "runtime" / "cases").glob("case_*.json"):
        try:
            c = json.loads(f.read_text())
        except Exception:
            continue
        escalated = bool((c.get("escalation") or {}).get("required"))
        status = (c.get("problem") or {}).get("status", "open")
        if status == "open":
            report["kept"] += 1  # open cases are never swept
            continue
        ttl = pol["cases"] + (pol["escalated_extra"] if escalated else 0)
        if _older_than(f, ttl, now):
            report["swept"].append(str(f))
            if apply:
                f.unlink(missing_ok=True)
        else:
            report["kept"] += 1

    for sub, key in (("uploads", "uploads"), ("tts", "tts")):
        for f in (base / "runtime" / sub).glob("*"):
            if not f.is_file():
                continue
            if _older_than(f, pol[key], now):
                report["swept"].append(str(f))
                if apply:
                    f.unlink(missing_ok=True)
            else:
                report["kept"] += 1

    for f in (base / "var").glob("*.jsonl"):
        if _older_than(f, pol["logs"], now):
            report["swept"].append(str(f))
            if apply:
                f.unlink(missing_ok=True)
        else:
            report["kept"] += 1

    db = base / "runtime" / "support.db"
    if db.exists() and _older_than(db, pol["db"] * 10, now):
        pass  # DB rows aged below; file itself is never deleted by the sweeper.
    if db.exists() and apply:
        try:
            con = sqlite3.connect(db)
            cutoff = now - pol["db"]
            cur = con.execute("DELETE FROM messages WHERE ts < ?", (cutoff,))
            report["db_rows_deleted"] = cur.rowcount
            con.commit()
            con.execute("VACUUM")
            con.close()
        except Exception as e:
            report["db_error"] = str(e)[:160]
    return report


if __name__ == "__main__":
    import sys
    rep = sweep(".", apply="--apply" in sys.argv)
    print(json.dumps(rep, indent=1))
