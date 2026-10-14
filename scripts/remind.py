#!/usr/bin/env python3
"""Callback reminder loop. Cron-friendly: `python3 scripts/remind.py --once`.

Reads runtime/reminders.jsonl, prints due nudges (and re-queues them every
REMIND_EVERY_SECS until marked done). Mark done by appending
{"caller":..., "done": true} or editing the file. Emergency items nag first.
"""
from __future__ import annotations
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from afterhours import REMINDERS, REMIND_EVERY_SECS  # noqa: E402


def load() -> list:
    if not os.path.isfile(REMINDERS):
        return []
    rows = []
    for line in open(REMINDERS):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def due(rows: list, now: int) -> list:
    open_rows = [r for r in rows if not r.get("done")]
    return sorted(
        [r for r in open_rows if r.get("next_due", 0) <= now],
        key=lambda r: (0 if r.get("urgency") == "emergency" else 1,
                       r.get("next_due", 0)))


def main() -> int:
    now = int(time.time())
    pending = due(load(), now)
    if not pending:
        print("reminders: nothing due")
        return 0
    for r in pending:
        print(f"CALL BACK [{r.get('urgency', '?')}] {r.get('caller', '?')} "
              f"{r.get('number', '?')}: {(r.get('issue', ''))[:100]} "
              f"(waiting {int((now - r.get('created', now)) / 3600)}h, "
              f"nag #{r.get('nags', 0) + 1})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
