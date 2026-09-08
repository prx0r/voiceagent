"""Tiered IT tools: safe diagnostics run free, fixes need a confirm
token from a prior proposal, critical classes refuse into a ticket.

Every call is audit-logged (who/what/tier/approved). This log is the
evidence trail — prompt-injection or tool-abuse review starts here.
"""
from __future__ import annotations
import json
import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path

AUDIT = Path(__file__).parent.parent / "var" / "it_audit.jsonl"
OUTSTANDING: dict[str, dict] = {}  # token -> {action, args, session, expires}

SAFE = {"disk_free", "network_status", "ping_gateway",
        "list_processes", "read_logs"}
MODERATE = {"restart_process", "clear_dns_cache", "clear_print_queue"}
REFUSE = ("delete", "rm ", "firewall", "password", "credential",
          "secret", "token", "format", "mkfs", "dd ")


def audit(session_id, tool, tier, args, result):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT, "a") as f:
        f.write(json.dumps({"t": time.time(), "session": session_id,
                            "tool": tool, "tier": tier, "args": args,
                            "ok": bool(result.get("ok"))}) + "\n")


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr or "")[:2000]
    except Exception as e:
        return f"unavailable: {e}"


def _refused_blob(args: dict) -> str:
    return json.dumps(args).lower()


def propose(session_id: str, action: str, args: dict) -> dict:
    """Step 1 of any fix: returns a confirm token the customer must echo."""
    if any(k in _refused_blob(args) for k in REFUSE):
        return {"ok": False, "tier": "critical",
                "error": "refused: needs a human technician (ticket it)."}
    tok = "confirm_" + secrets.token_hex(4)
    OUTSTANDING[tok] = {"action": action, "args": args,
                        "session": session_id, "expires": time.time() + 600}
    return {"ok": True, "tier": "moderate", "confirm_token": tok,
            "message": f"Proposed {action}. Customer must confirm with: {tok}"}


def execute(session_id: str, confirm_token: str) -> dict:
    """Step 2: run a previously proposed fix. Token single-use, 10 min."""
    job = OUTSTANDING.pop(confirm_token, None)
    if job is None or job["session"] != session_id or job["expires"] < time.time():
        return {"ok": False, "error": "bad or expired confirm token — propose again."}
    action, args = job["action"], job["args"]
    if action == "restart_process":
        name = str(args.get("process", ""))[:64]
        if not name:
            return {"ok": False, "error": "process required"}
        out = _run(["pkill", "-f", name]) or "signal sent"
        return {"ok": True, "tier": "moderate", "action": action, "result": out[:200]}
    if action == "clear_dns_cache":
        if shutil.which("resolvectl"):
            out = _run(["resolvectl", "flush-caches"])
            ok = "unavailable" not in out
            return {"ok": ok, "tier": "moderate", "action": action,
                    "result": (out[:200] or "flushed") if ok else out[:200]}
        if shutil.which("systemd-resolve"):
            out = _run(["systemd-resolve", "--flush-caches"])
            ok = "unavailable" not in out
            return {"ok": ok, "tier": "moderate", "action": action,
                    "result": (out[:200] or "flushed") if ok else out[:200]}
        return {"ok": False, "tier": "moderate", "action": action,
                "result": "no DNS flush tool on this machine — ticket it."}
    if action == "clear_print_queue":
        out = _run(["cancel", "-a"]) or "queue cleared"
        return {"ok": True, "tier": "moderate", "action": action, "result": out[:200]}
    return {"ok": False, "error": f"unknown fix action: {action}"}


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
        return {"ok": True, "tier": "safe", "host": host,
                "result": _run(["ping", "-c", "3", "-W", "2", host])[:500]}
    if tool == "list_processes":
        name = str(args.get("name", ""))[:64]
        cmd = ["pgrep", "-af", name] if name else ["ps", "-eo", "comm", "--sort=-%cpu"]
        return {"ok": True, "tier": "safe", "result": _run(cmd)[:1000]}
    if tool == "read_logs":
        unit = str(args.get("unit", ""))[:64]
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
    "execute_fix": "STEP 2: run a proposed fix. args: confirm_token (customer must echo it).",
}
