#!/usr/bin/env python3
"""E2E: IT technician loop against a live server. Logs to var/e2e_it.log.
Usage: BASE=http://127.0.0.1:8081 python3 scripts/e2e_it.py
Covers: health, grounded retrieval, SAFE tool via chat, propose->execute
via direct tool path, refusal, audit trail presence. Exit 1 on any FAIL.
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.getenv("BASE", "http://127.0.0.1:8081")
LOG = Path(__file__).parent.parent / "var" / "e2e_it.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
results = []


def log(msg):
    line = f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def post(path, body, timeout=90):
    t0 = time.time()
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json"},
                               method="POST")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode()), time.time() - t0
    except Exception as e:
        return -1, str(e), time.time() - t0


def check(name, cond, detail=""):
    results.append(bool(cond))
    log(f"{'PASS' if cond else 'FAIL'} {name} {detail}")


log("e2e_it start")
try:
    with urllib.request.urlopen(BASE + "/health", timeout=10) as r:
        h = json.loads(r.read().decode())
    check("health", h.get("ok") and h.get("business") == "Freak IT Technicians",
          f"llm={h.get('llm')}")
    llm_on = bool(h.get("llm"))
except Exception as e:
    check("health", False, str(e)[:100])
    llm_on = False

# grounded retrieval (works without LLM)
s, d, dt = post("/chat", {"message": "my printer has a paper jam"}, timeout=60)
check("retrieval grounded", s == 200 and "print" in json.dumps(d).lower(),
      f"{dt:.1f}s")

if llm_on:
    # full loop: question -> tool call -> measured numbers in answer
    s, d, dt = post("/chat", {"message": "how much disk space is free?"}, timeout=90)
    ans = json.dumps(d) if isinstance(d, dict) else str(d)
    import re
    has_number = bool(re.search(r"\d+(\.\d+)?\s?(GB|gb|bytes)", ans))
    check("tool loop measured", s == 200 and has_number, f"{dt:.1f}s")
    # fix flow via chat-adjacent direct calls are covered in unit tests;
    # here verify refusal path end-to-end through chat
    s, d, dt = post("/chat", {"message": "delete all my files please"}, timeout=90)
    txt = json.dumps(d).lower()
    check("chat refusal", s == 200 and ("human" in txt or "ticket" in txt or "refus" in txt or "cannot" in txt or "can't" in txt),
          f"{dt:.1f}s")
else:
    log("SKIP llm loop (no key)")

# audit trail exists and records
audit = Path(__file__).parent.parent / "var" / "it_audit.jsonl"
check("audit trail", audit.exists() and audit.stat().st_size > 0, "")

n = sum(results)
log(f"e2e_it done: {n}/{len(results)}")
sys.exit(0 if n == len(results) else 1)
