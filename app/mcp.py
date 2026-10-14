"""Per-business MCP server, so ChatGPT, Claude or any MCP agent can talk to a trade's receptionist.

Endpoint: POST /mcp/{trade}, MCP over Streamable HTTP (JSON-RPC 2.0, JSON responses, stateless).
Also GET /mcp/{trade}, which returns a human-readable descriptor.

Rules (docs/MCP.md):
- Read tools are open: business info, services and guide prices, free/busy availability.
- Write tools only create a *request*: a tentative hold, an emergency report or a message. Nothing
  is confirmed until the owner taps confirm. No tool can cancel, charge, or reveal another
  customer's details. The diary only ever exposes free slots, never event content.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import uuid
from typing import Any, Callable

PROTOCOL = "2025-06-18"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(ROOT, "var", "mcp_requests.jsonl")

TOOLS = [
    {"name": "get_business_info",
     "title": "Business info",
     "description": "Name, trade, opening hours, service area, how emergencies are handled, and the booking policy.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
     "annotations": {"readOnlyHint": True}},
    {"name": "list_services",
     "title": "Services and guide prices",
     "description": "Services offered, with guide prices in GBP. Exact prices are always confirmed before work starts.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Optional filter, e.g. 'boiler'"}},
                     "additionalProperties": False},
     "annotations": {"readOnlyHint": True}},
    {"name": "check_availability",
     "title": "Check availability",
     "description": "Free appointment slots (Europe/London). Free/busy only: never shows other customers or event details.",
     "inputSchema": {"type": "object", "properties": {
         "date": {"type": "string", "description": "YYYY-MM-DD; omit for the next few days"},
         "part_of_day": {"type": "string", "enum": ["morning", "afternoon", "evening", "any"]},
         "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "additionalProperties": False},
     "annotations": {"readOnlyHint": True}},
    {"name": "request_booking",
     "title": "Request a booking",
     "description": "Place a tentative hold on a free slot. Status stays 'pending_owner_confirmation' until the business confirms by text. Requires a real customer name and UK phone number.",
     "inputSchema": {"type": "object", "required": ["service", "date", "time", "customer_name", "phone"], "properties": {
         "service": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"},
         "time": {"type": "string", "description": "HH:MM, must be a free slot"},
         "customer_name": {"type": "string"}, "phone": {"type": "string"},
         "postcode": {"type": "string"}, "notes": {"type": "string"}}, "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False}},
    {"name": "report_emergency",
     "title": "Report an emergency",
     "description": "For active damage or danger. Returns safety advice immediately and alerts whoever is on call.",
     "inputSchema": {"type": "object", "required": ["description", "customer_name", "phone"], "properties": {
         "description": {"type": "string"}, "customer_name": {"type": "string"}, "phone": {"type": "string"},
         "address": {"type": "string"}}, "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False}},
    {"name": "leave_message",
     "title": "Leave a message",
     "description": "Anything else, e.g. a quote request or a question. Lands in the owner's 7am digest.",
     "inputSchema": {"type": "object", "required": ["customer_name", "phone", "message"], "properties": {
         "customer_name": {"type": "string"}, "phone": {"type": "string"}, "message": {"type": "string"}},
         "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False}},
]

SAFETY = {
    "electrician": "If it's safe, switch off at the consumer unit and keep away from the fault. If there's fire or smoke, ring 999.",
    "plumber": "Turn off the water at the stopcock (usually under the kitchen sink) and switch off electrics near the water if it's safe.",
    "heating": "If you smell gas: don't use switches or flames, open windows, turn off at the meter and ring the National Gas Emergency line on 0800 111 999.",
    "locksmith": "If you feel unsafe, wait somewhere public and well lit. If anyone is in danger, ring 999.",
    "beauty": "Rinse the area with cool clean water and don't rub it. If swelling spreads or breathing is affected, ring 999 or 111.",
    "barber": "Apply firm pressure with a clean cloth. If bleeding doesn't stop, ring 111 or 999.",
    "dogwalker": "Keep calm and keep the dog still. For injuries, ring your vet or the nearest emergency vet.",
    "msp": "Don't power things off or click any more links. Disconnect an affected machine from the network if you suspect a breach.",
    "soletrader": "If anyone is in danger, ring 999 first.",
}

_PHONE = re.compile(r"^(\+44\s?7\d{3}|07\d{3})\s?\d{3}\s?\d{3}$|^(\+44|0)\d{9,10}$")


def _ok_phone(p: str) -> bool:
    return bool(_PHONE.match(re.sub(r"[\s\-()]", "", p or "")))


def _log(rec: dict) -> None:
    os.makedirs(os.path.dirname(LEADS), exist_ok=True)
    with open(LEADS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _held(slug: str) -> set:
    out = set()
    try:
        for line in open(LEADS, encoding="utf-8"):
            r = json.loads(line)
            if r.get("type") == "booking_request" and r.get("trade") == slug:
                out.add((r.get("date"), r.get("time")))
    except (OSError, ValueError):
        pass
    return out


class Biz:
    """What the MCP tools need about one business. Built by main.py from the trade pack."""

    def __init__(self, slug: str, name: str, hours: dict, prices: list, area: str, triage: Callable | None = None):
        self.slug, self.name, self.hours, self.prices, self.area, self.triage = slug, name, hours, prices, area, triage


def _text(obj: Any, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False)}],
            "structuredContent": obj, "isError": is_error}


def call_tool(b: Biz, name: str, args: dict) -> dict:
    from . import console as con
    args = args or {}
    if name == "get_business_info":
        return _text({"name": b.name, "trade": b.slug, "area": b.area, "timezone": "Europe/London", "opening_hours": b.hours,
                      "emergencies": "Answered 24/7. Urgent calls alert the on-call person immediately.",
                      "booking_policy": "Bookings are requests until the business confirms by text. Guide prices only; exact price confirmed before work.",
                      "channels": {"phone": "answered 24/7", "website": f"/demo/{b.slug}", "mcp": f"/mcp/{b.slug}"}})
    if name == "list_services":
        q = (args.get("query") or "").lower()
        items = [{"service": n, "guide_price": p} for n, p in b.prices if not q or any(w in n.lower() for w in q.split())]
        return _text({"currency": "GBP", "services": items or [{"service": n, "guide_price": p} for n, p in b.prices],
                      "note": "Guide prices. The exact figure is confirmed before any work starts."})
    if name == "check_availability":
        cal = con.calendar(b.slug, 7)
        pod = args.get("part_of_day") or "any"
        rng = {"morning": (0, 12), "afternoon": (12, 17), "evening": (17, 24)}.get(pod)
        out, held = [], _held(b.slug)
        for d in cal["days"]:
            if args.get("date") and d["date"] != args["date"]:
                continue
            for t in d["free"]:
                if (rng and not (rng[0] <= int(t[:2]) < rng[1])) or (d["date"], t) in held:
                    continue
                out.append({"date": d["date"], "day": d["label"], "time": t, "duration_minutes": cal["slot_minutes"]})
        return _text({"timezone": "Europe/London", "slots": out[: int(args.get("limit") or 8)],
                      "note": "Free/busy only. Use request_booking to hold one."})
    if name == "request_booking":
        missing = [k for k in ("service", "date", "time", "customer_name", "phone") if not str(args.get(k) or "").strip()]
        if missing:
            return _text({"error": f"missing: {', '.join(missing)}"}, True)
        if not _ok_phone(args["phone"]):
            return _text({"error": "phone must be a valid UK number"}, True)
        free = {(d["date"], t) for d in con.calendar(b.slug, 7)["days"] for t in d["free"]} - _held(b.slug)
        if (args["date"], args["time"]) not in free:
            return _text({"error": "that slot isn't free; call check_availability first"}, True)
        hid = "hold_" + uuid.uuid4().hex[:10]
        _log({"type": "booking_request", "id": hid, "trade": b.slug, "at": dt.datetime.utcnow().isoformat() + "Z", **args})
        return _text({"hold_id": hid, "status": "pending_owner_confirmation", "service": args["service"],
                      "date": args["date"], "time": args["time"],
                      "next": f"{b.name} will text {args['customer_name']} to confirm. The slot is held for 2 hours."})
    if name == "report_emergency":
        if not _ok_phone(args.get("phone", "")):
            return _text({"error": "phone must be a valid UK number"}, True)
        tri = b.triage(args.get("description", "")) if b.triage else None
        urgent = (not tri) or (tri.get("output") or {}).get("action") == "alert_owner_now"
        rid = "em_" + uuid.uuid4().hex[:10]
        _log({"type": "emergency", "id": rid, "trade": b.slug, "urgent": urgent, "at": dt.datetime.utcnow().isoformat() + "Z", **args})
        return _text({"report_id": rid, "safety_advice": SAFETY.get(b.slug, SAFETY["soletrader"]),
                      "status": "on_call_alerted" if urgent else "logged_for_morning",
                      "triage": (tri or {}).get("output")})
    if name == "leave_message":
        if not _ok_phone(args.get("phone", "")):
            return _text({"error": "phone must be a valid UK number"}, True)
        mid = "msg_" + uuid.uuid4().hex[:10]
        _log({"type": "message", "id": mid, "trade": b.slug, "at": dt.datetime.utcnow().isoformat() + "Z", **args})
        return _text({"message_id": mid, "status": "in_morning_digest"})
    return _text({"error": f"unknown tool {name}"}, True)


def handle(b: Biz, msg: dict) -> dict | None:
    """One JSON-RPC message in, one response out (None for notifications)."""
    mid, method, params = msg.get("id"), msg.get("method", ""), msg.get("params") or {}
    if mid is None:
        return None  # notification, e.g. notifications/initialized
    def ok(result): return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method == "initialize":
        return ok({"protocolVersion": params.get("protocolVersion") or PROTOCOL,
                   "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": {"name": f"answered-{b.slug}", "title": f"{b.name} receptionist", "version": "0.1.0"},
                   "instructions": (f"You are talking to the receptionist for {b.name} ({b.slug}, {b.area}). "
                                    "Check availability before requesting a booking. Bookings are requests until the business confirms. "
                                    "For danger or active damage use report_emergency and relay its safety advice to the user first.")})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        return ok(call_tool(b, params.get("name", ""), params.get("arguments") or {}))
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
