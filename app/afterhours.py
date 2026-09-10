"""After-hours workflow. The money workflow:

  inbound call/text (transcript) -> triage_urgency -> case (full log)
  -> wake_now? alert : queue digest with one-click actions:
     proposed morning slots (calendar-aware), draft reply, rough quote,
     worth-it score, parts check (approval-gated).

Pure-ish: takes stores/paths as args so tests use tmp dirs.
"""
from __future__ import annotations
import time
import uuid
from typing import Any

from . import cases as casekit
from . import evtools
from . import tradie as tradiekit
from . import parts as partskit
from tools import calendar as cal


def format_transcript(transcript: str, meta: dict) -> str:
    """Canonical transcript block. Pure — same input, same output, testable."""
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    who = meta.get("name") or meta.get("phone") or "unknown caller"
    ch = meta.get("channel", "voice")
    return f"[{ts} {ch} {who}] {(transcript or '').strip()}"


def intake_call(transcript: str, meta: dict, case_store, profile: dict,
                tickets: list | None = None) -> dict:
    """Handle one overnight contact. Returns digest item (what sparky sees)."""
    meta = meta or {}
    tri = evtools.triage_urgency(
        transcript, hour=meta.get("hour"), vulnerable=bool(meta.get("vulnerable")))
    level = tri.get("level", "routine")

    case = casekit.new_case(meta.get("phone", "") or meta.get("name", ""),
                            meta.get("channel", "voice"))
    casekit.apply(case, {"type": "intent.set",
                         "payload": {"intent": "AFTERHOURS_" + level.upper()}})
    casekit.apply(case, {"type": "problem.updated",
                         "payload": {"description": transcript[:500],
                                     "status": "open"}})
    casekit.apply(case, {"type": "observation.added",
                         "payload": {"otype": "transcript",
                                     "value": format_transcript(transcript, meta)[:500],
                                     "confidence": 0.9}})
    # Missed-call-only routing receipt: who answered and why the agent has it.
    # (Telephony layer forwards after RINGS_BEFORE_TAKEOVER rings; see README.)
    # Without this note the morning queue can't prove caught-vs-voicemail value.
    answered_by = meta.get("answered_by", "agent")
    mode = (profile.get("preferences") or {}).get("answer_mode", "always")
    rings = (profile.get("preferences") or {}).get("rings_before_takeover", 5)
    casekit.apply(case, {"type": "observation.added",
                         "payload": {"otype": "route",
                                     "value": (f"mode={mode} answered_by={answered_by} "
                                               f"(rings={rings}) — would-be voicemail"
                                               if answered_by == "agent" else
                                               f"mode={mode} answered_by=human — "
                                               f"logged for record"),
                                     "confidence": 1.0}})
    casekit.apply(case, {"type": "observation.added",
                         "payload": {"otype": "triage",
                                     "value": f"{level}: {tri.get('reason','')}",
                                     "confidence": 0.8}})

    cal_path = ((profile.get("calendar") or {}).get("file")
                or "runtime/calendar.json")
    prefs = profile.get("preferences") or {}
    day = meta.get("day")  # 'YYYY-MM-DD' or None -> propose generic
    slots = cal.free_slots(
        cal_path, day, mornings_first=bool(prefs.get("mornings_first", True)),
        slot_min=int((profile.get("calendar") or {}).get("slot_min", 60)),
        buffer_min=int((profile.get("calendar") or {}).get("buffer_min", 30)),
    ) if day else []
    job = {"name": meta.get("name", ""), "postcode": meta.get("postcode", ""),
           "summary": transcript, "charger": meta.get("charger", ""),
           "value_gbp": meta.get("value_gbp", 300),
           "ease": meta.get("ease", "medium"),
           "slot_is_morning": bool(slots and int(slots[0][11:13]) < 12)}
    worth = tradiekit.worth_it(profile, job)
    draft = tradiekit.draft_quote(
        profile, {**job, "proposed_slots": slots},
        parts_total=float(meta.get("parts_total", 0) or 0))
    draft_text = draft["text"]
    if evtools.network_suspected(transcript):
        draft_text += (" If the whole street is out, that's the network not your "
                       "wiring — free call 105 and they'll tell you.")
        casekit.apply(case, {"type": "observation.added",
                             "payload": {"otype": "network",
                                         "value": "suspected network outage, 105 advised",
                                         "confidence": 0.7}})
    parts_info: dict[str, Any] = {}
    if meta.get("parts"):
        chk = partskit.check(meta["parts"])
        parts_info = chk
        casekit.apply(case, {"type": "observation.added",
                             "payload": {"otype": "parts",
                                         "value": str(chk)[:400],
                                         "confidence": 1.0}})

    actions = _actions_for(level, slots, bool(parts_info.get("ok")),
                           parts_info.get("delay_days", 0) if parts_info else 0)
    if level == "wake_now":
        casekit.apply(case, {"type": "escalation.requested",
                             "payload": {"reason": tri.get("reason", "urgent")}})
        alert = {"wake": True, "via": ["push", "sms"],
                 "text": f"URGENT {meta.get('name','caller')}: {transcript[:140]}"}
    else:
        alert = {"wake": False, "via": ["digest"], "text": "queued for morning"}
    casekit.apply(case, {"type": "handoff.note",
                         "payload": {"note": (
                             f"worth {worth['score']} ({worth['verdict']}); "
                             f"draft: {draft['text']}"[:450])}})
    # Lifecycle stage: the case always says what happens next.
    case["next_required"] = ("call back now — woken engineer" if level == "wake_now"
                             else "sparky morning review → book / reply / close")
    case_store.save(case)
    if tickets is not None and level != "wake_now":
        tickets.append({"case_id": case["case_id"], "level": level})

    return {"case_id": case["case_id"], "level": level,
            "reason": tri.get("reason", ""), "transcript": transcript[:500],
            "wake": alert, "proposed_slots": slots,
            "draft_response": draft_text, "quote_range": draft["range"],
            "worth_it": worth, "parts": parts_info, "actions": actions,
            "t": time.time()}


def _actions_for(level: str, slots: list, parts_ok: bool,
                 delay_days: int) -> list[dict]:
    acts = []
    if slots:
        acts.append({"id": "book_first_slot",
                     "label": f"Book {slots[0]}",
                     "kind": "calendar"})
        if len(slots) > 1:
            acts.append({"id": "offer_slots",
                         "label": f"Offer {len(slots)} times to customer",
                         "kind": "message"})
    else:
        acts.append({"id": "offer_callback",
                     "label": "Offer callback tomorrow",
                     "kind": "message"})
    acts.append({"id": "send_draft", "label": "Send draft reply",
                 "kind": "message"})
    if parts_ok:
        acts.append({"id": "approve_parts",
                     "label": "Approve parts order" + (
                         f" ({delay_days}d lead)" if delay_days else ""),
                     "kind": "approval"})
    acts.append({"id": "on_my_way",
                 "label": "Notify customer when en route",
                 "kind": "message"})
    if level == "wake_now":
        acts.insert(0, {"id": "call_back_now", "label": "Call back now",
                        "kind": "urgent"})
    return acts


def morning_digest(case_store, profile: dict, since_ts: float = 0) -> list[dict]:
    """Overnight queue for the sparky app. Newest urgent first."""
    import json
    items = []
    for f in sorted(case_store.path.glob("case_*.json")):
        try:
            c = json.loads(f.read_text())
        except Exception:
            continue
        if c.get("created_at", 0) < since_ts:
            continue
        if c.get("channel") not in ("voice", "whatsapp", "ev-funnel", "web"):
            continue
        obs = {o.get("type"): o.get("value", "") for o in c.get("observations", [])}
        items.append({
            "case_id": c["case_id"],
            "channel": c.get("channel"),
            "transcript": obs.get("transcript", "")[:300],
            "triage": obs.get("triage", ""),
            "escalated": bool(c.get("escalation", {}).get("required")),
            "brief": case_store.brief(c["case_id"])[:600],
        })
    items.sort(key=lambda i: (not i["escalated"], i["case_id"]))
    return items


def catch_report(case_store, since_ts: float = 0) -> dict:
    """Caught-vs-voicemail proof: calls the agent handled that no human touched.

    (Human-answered calls never reach us, so the denominator is voicemail-bound
    calls, not all calls. Report it honestly: 'caught N that would've been
    voicemail, X urgent among them'.)
    """
    import json
    caught, urgent, by_level = 0, 0, {}
    for f in sorted(case_store.path.glob("case_*.json")):
        try:
            c = json.loads(f.read_text())
        except Exception:
            continue
        if c.get("created_at", 0) < since_ts:
            continue
        routes = [o.get("value", "") for o in c.get("observations", [])
                  if o.get("type") == "route"]
        if any("answered_by=agent" in r for r in routes):
            caught += 1
            tri = next((o.get("value", "") for o in c.get("observations", [])
                        if o.get("type") == "triage"), "")
            lvl = tri.split(":")[0] if ":" in tri else "routine"
            by_level[lvl] = by_level.get(lvl, 0) + 1
            if c.get("escalation", {}).get("required"):
                urgent += 1
    return {"caught": caught, "urgent": urgent, "by_level": by_level}
