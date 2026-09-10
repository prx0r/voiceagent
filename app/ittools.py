"""Tiered IT tools: safe diagnostics run free, fixes need a confirm
token from a prior proposal, critical classes refuse into a ticket.

Every call is audit-logged (who/what/tier/approved). This log is the
evidence trail — prompt-injection or tool-abuse review starts here.
"""
from __future__ import annotations
import json
import os
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import time
from pathlib import Path

AUDIT = Path(__file__).parent.parent / "var" / "it_audit.jsonl"
STATE_DB = Path(__file__).parent.parent / "runtime" / "ittools_state.db"
OUTSTANDING: dict[str, dict] = {}  # token -> {action, args, session, expires}
SEEN_KEYS: dict[str, dict] = {}  # idempotency_key -> result (receipt replay)
ATTEMPTS: dict[str, list] = {}  # session -> [timestamps] for execute rate limit

SAFE = {"disk_free", "network_status", "ping_gateway",
        "list_processes", "read_logs"}
MODERATE = {"restart_process", "clear_dns_cache", "clear_print_queue"}
REFUSE = ("delete", "rm ", "firewall", "password", "pass_word", "passwd",
          "credential", "secret", "token", "format", "mkfs", "dd ")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,64}$")
UNIT_RE = re.compile(r"^[a-z0-9@:_.-]{0,64}$")
EXECUTE_LIMIT = 5  # max execute attempts per session per 10 min window


def restart_allowlist() -> set:
    return {x.strip() for x in
            os.getenv("IT_RESTART_ALLOWLIST", "").split(",") if x.strip()}


def _state():
    """SQLite backing so restarts don't brick pending fixes or receipts."""
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STATE_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS outstanding(
      token TEXT PRIMARY KEY, session TEXT, action TEXT, args TEXT, exp REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS receipts(
      key TEXT PRIMARY KEY, session TEXT, result TEXT, ts REAL)""")
    return con


def audit(session_id, tool, tier, args, result):
    from .pii import scrub_all
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    line = scrub_all(json.dumps({"t": time.time(), "session": session_id,
                                 "tool": tool, "tier": tier, "args": args,
                                 "ok": bool(result.get("ok"))}))
    with open(AUDIT, "a") as f:
        f.write(line + "\n")


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr or "")[:2000]
    except Exception as e:
        return f"unavailable: {e}"


def _refused_blob(action: str, args: dict) -> str:
    # Scan the ACTION name too, not just args (pass_word-style bypasses).
    return f"{action} {json.dumps(args)}".lower()


def propose(session_id: str, action: str, args: dict) -> dict:
    """Step 1 of any fix: returns a confirm token the customer must echo."""
    if any(k in _refused_blob(action, args) for k in REFUSE):
        return {"ok": False, "tier": "critical",
                "error": "refused: needs a human technician (ticket it)."}
    if action == "restart_process":
        # Default-deny: only explicitly allowlisted process names restart.
        name = str((args or {}).get("process", "")).strip()
        if name not in restart_allowlist():
            return {"ok": False, "tier": "moderate",
                    "error": "restart target not allowlisted — ticket it for a human."}
    tok = "confirm_" + secrets.token_hex(16)  # 128-bit
    job = {"action": action, "args": args,
           "session": session_id, "expires": time.time() + 600}
    OUTSTANDING[tok] = job
    try:
        con = _state()
        con.execute("INSERT OR REPLACE INTO outstanding VALUES(?,?,?,?,?)",
                    (tok, session_id, action, json.dumps(args), job["expires"]))
        con.commit()
        con.close()
    except Exception:
        pass  # memory copy still enforces single-use this process
    return {"ok": True, "tier": "moderate", "confirm_token": tok,
            "message": f"Proposed {action}. Customer must confirm with: {tok}"}


def _rate_ok(session_id: str) -> bool:
    now = time.time()
    hits = [t for t in ATTEMPTS.get(session_id, []) if now - t < 600]
    hits.append(now)
    ATTEMPTS[session_id] = hits
    return len(hits) <= EXECUTE_LIMIT


def _pop_token(confirm_token: str):
    job = OUTSTANDING.pop(confirm_token, None)
    try:
        con = _state()
        row = con.execute("SELECT session,action,args,exp FROM outstanding WHERE token=?",
                          (confirm_token,)).fetchone()
        con.execute("DELETE FROM outstanding WHERE token=?", (confirm_token,))
        con.commit()
        con.close()
        if job is None and row:
            job = {"action": row[1], "args": json.loads(row[2]),
                   "session": row[0], "expires": row[3]}
    except Exception:
        pass
    return job


def _recall(key: str, session_id: str):
    if key and key in SEEN_KEYS:
        old = dict(SEEN_KEYS[key])
        old["replayed"] = True
        return old
    try:
        con = _state()
        row = con.execute("SELECT session,result FROM receipts WHERE key=?",
                          (key,)).fetchone()
        con.close()
        if row and row[0] == session_id:
            old = json.loads(row[1])
            old["replayed"] = True
            return old
    except Exception:
        pass
    return None


def execute(session_id: str, confirm_token: str,
            idempotency_key: str = "") -> dict:
    """Step 2: run a previously proposed fix. Token single-use, 10 min.
    Repeat callers pass the same idempotency_key and get the original
    receipt instead of a second execution."""
    if not _rate_ok(session_id):
        return {"ok": False, "error": "too many attempts — slow down or ticket it."}
    if idempotency_key:
        old = _recall(idempotency_key, session_id)
        if old:
            return old
    job = _pop_token(confirm_token)
    if job is None or job["session"] != session_id or job["expires"] < time.time():
        return {"ok": False, "error": "bad or expired confirm token — propose again."}
    action, args = job["action"], job["args"]
    if action == "restart_process":
        name = str(args.get("process", ""))[:64]
        if not name:
            return {"ok": False, "error": "process required"}
        if name.strip() not in restart_allowlist():
            return {"ok": False, "error": "restart target not allowlisted — ticket it."}
        out = _run(["pkill", "-f", name]) or "signal sent"
        return _receipt(session_id, idempotency_key,
                        {"ok": True, "tier": "moderate", "action": action,
                         "result": out[:200]})
    if action == "clear_dns_cache":
        if shutil.which("resolvectl"):
            out = _run(["resolvectl", "flush-caches"])
            ok = "unavailable" not in out
            return _receipt(session_id, idempotency_key,
                            {"ok": ok, "tier": "moderate", "action": action,
                             "result": (out[:200] or "flushed") if ok else out[:200]})
        if shutil.which("systemd-resolve"):
            out = _run(["systemd-resolve", "--flush-caches"])
            ok = "unavailable" not in out
            return _receipt(session_id, idempotency_key,
                            {"ok": ok, "tier": "moderate", "action": action,
                             "result": (out[:200] or "flushed") if ok else out[:200]})
        return {"ok": False, "tier": "moderate", "action": action,
                "result": "no DNS flush tool on this machine — ticket it."}
    if action == "clear_print_queue":
        out = _run(["cancel", "-a"]) or "queue cleared"
        return _receipt(session_id, idempotency_key,
                        {"ok": True, "tier": "moderate", "action": action,
                         "result": out[:200]})
    return {"ok": False, "error": f"unknown fix action: {action}"}


def _receipt(session_id: str, idempotency_key: str, result: dict) -> dict:
    """Stamp + store the receipt so retries replay instead of re-executing."""
    result["idempotency_key"] = idempotency_key
    if idempotency_key:
        SEEN_KEYS[idempotency_key] = dict(result)
        try:
            con = _state()
            con.execute("INSERT OR REPLACE INTO receipts VALUES(?,?,?,?)",
                        (idempotency_key, session_id, json.dumps(result),
                         time.time()))
            con.commit()
            con.close()
        except Exception:
            pass
    return result


def diagnose(tool: str, args: dict) -> dict:
    """SAFE tier: read-only, no confirmation needed."""
    if tool == "disk_free":
        total, used, free = shutil.disk_usage("/")
        gb = 1024 ** 3
        return {"ok": True, "tier": "safe",
                "free_gb": round(free / gb, 1), "used_gb": round(used / gb, 1)}
    if tool == "network_status":
        out = {"ok": True, "tier": "safe"}
        try:
            out["hostname"] = socket.gethostname()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            out["local_ip"] = s.getsockname()[0]
            s.close()
        except Exception as e:
            out["local_ip"] = f"unknown ({e})"
        out["gateway_route"] = _run(["ip", "route", "show", "default"])[:200]
        return out
    if tool == "ping_gateway":
        host = str(args.get("host", "8.8.8.8"))[:64]
        if not HOST_RE.fullmatch(host):
            return {"ok": False, "error": "bad host — plain hostname or IP only"}
        return {"ok": True, "tier": "safe", "host": host,
                "result": _run(["ping", "-c", "3", "-W", "2", host])[:500]}
    if tool == "list_processes":
        name = str(args.get("name", ""))[:64]
        cmd = ["pgrep", "-af", name] if name else ["ps", "-eo", "comm", "--sort=-%cpu"]
        return {"ok": True, "tier": "safe", "result": _run(cmd)[:1000]}
    if tool == "read_logs":
        unit = str(args.get("unit", ""))[:64]
        if not UNIT_RE.fullmatch(unit):
            return {"ok": False, "error": "bad unit — systemd name only"}
        cmd = (["journalctl", "-u", unit, "-n", "20", "--no-pager"] if unit
               else ["journalctl", "-p", "err", "-n", "20", "--no-pager"])
        return {"ok": True, "tier": "safe", "result": _run(cmd)[:1500]}
    return {"ok": False, "error": f"unknown diagnostic: {tool}"}


DESCRIPTIONS = {
    "disk_free": "Free/used disk space. args: none",
    "network_status": "Local IP, hostname, default route. args: none",
    "ping_gateway": "Ping a host (default 8.8.8.8). args: host?",
    "list_processes": "List processes, optional name filter. args: name?",
    "read_logs": "Recent error logs, optional systemd unit. args: unit?",
    "propose_fix": "STEP 1: propose a fix, get confirm token. args: action (restart_process|clear_dns_cache|clear_print_queue), plus action args. Refusals (delete/security/credentials) come back critical.",
    "execute_fix": "STEP 2: run a proposed fix. args: confirm_token (customer must echo it), idempotency_key? (repeat callers get the original receipt).",
}
