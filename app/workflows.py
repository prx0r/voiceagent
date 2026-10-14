"""Bridge to AgentRun workflows (workflows/*.json) with Jev typed decisions via OpenRouter.

Runs `node workflows/triage.mjs <name>` with JSON on stdin. Optional: if node, the
packages or the key are missing, or anything fails or is slow, returns None and the
caller keeps its rule-based path. Credentials stay in .env (gitignored).
"""
from __future__ import annotations
import json
import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WF = os.path.join(ROOT, "workflows")
_CACHE: dict = {}


def enabled() -> bool:
    if not os.path.isdir(os.path.join(WF, "node_modules", "@parcha")):
        return False
    if os.getenv("TYPESAFE_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
        return True
    try:
        return "TYPESAFE_API_KEY=" in open(os.path.join(ROOT, ".env")).read()
    except OSError:
        return False


def run(name: str, payload: dict, timeout: float = 6.0) -> dict | None:
    if not enabled():
        return None
    key = (name, json.dumps(payload, sort_keys=True))
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    try:
        p = subprocess.run(["node", "triage.mjs", name], cwd=WF, input=json.dumps(payload),
                           capture_output=True, text=True, timeout=timeout)
        out = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return None
    if not out.get("ok"):
        return None
    if len(_CACHE) > 500:
        _CACHE.clear()
    _CACHE[key] = (time.time(), out)
    return out


def triage(trade: str, business: str, message: str) -> dict | None:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Europe/London")).strftime("%H:%M")
    return run("call-triage", {"trade": trade, "business": business, "message": message[:600], "local_time": now})
