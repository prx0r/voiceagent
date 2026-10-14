"""Product site data: industries + global services, derived from packs.

Packs stay the source of truth (services, pricing, escalation). This module
only adds display labels/taglines per trade. Placeholders are never shown:
trade-level copy is static, business names come from onboarding later.
"""
from __future__ import annotations
import os
import re
import yaml

KNOWLEDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "knowledge")

TRADES = [
    {"slug": "electrician", "file": "sparky_electrician_en.yaml",
     "label": "Electricians", "icon": "⚡",
     "tagline": "Sparks and burning smells don't wait for morning. Neither do we."},
    {"slug": "plumber", "file": "flowright_plumbing_en.yaml",
     "label": "Plumbers", "icon": "🔧",
     "tagline": "Burst pipes call at 2am. We pick up; you sleep."},
    {"slug": "heating", "file": "trades_heating_uk.yaml",
     "label": "Heating Engineers", "icon": "🔥",
     "tagline": "Dead boilers in winter. Answered in your voice, escalated in minutes."},
    {"slug": "locksmith", "file": "trades_locksmith_uk.yaml",
     "label": "Locksmiths", "icon": "🔑",
     "tagline": "Locked out at midnight. Verified, quoted, dispatched."},
    {"slug": "beauty", "file": "beauty_gb.yaml",
     "label": "Beauty & Salons", "icon": "💅",
     "tagline": "Bookings taken mid-treatment. No-shows chased automatically."},
    {"slug": "barber", "file": "barber_gb.yaml",
     "label": "Barbers", "icon": "💈",
     "tagline": "Walk-ins and bookings while the clippers run."},
    {"slug": "dogwalker", "file": "petcare_gb.yaml",
     "label": "Dog Walkers & Pet Care", "icon": "🐕",
     "tagline": "Hands full of Labradors. We take the calls."},
    {"slug": "msp", "file": "msp_gb.yaml",
     "label": "IT & MSP", "icon": "🖥️",
     "tagline": "Tier-1 triage and training sims for your helpdesk."},
    {"slug": "soletrader", "file": "trades_soletrader_uk.yaml",
     "label": "Something else?", "icon": "🧰",
     "tagline": "Any sole trade, live in 20 minutes."},
]

CORE_SERVICES = [
    {"icon": "📞", "title": "After-hours answering, in your voice",
     "text": "Your cloned voice answers every missed call, discloses itself, and runs your trade's intake. 50p per active minute, nothing else."},
    {"icon": "⚡", "title": "Instant owner alerts",
     "text": "Emergencies fire SMS + WhatsApp immediately. Everything else lands in one 7am email digest with transcripts and notes."},
    {"icon": "🔁", "title": "Callback reminders that nag",
     "text": "Every unanswered caller re-surfaces every 2 hours until marked done. No-callback 1-star reviews stop here."},
    {"icon": "🎓", "title": "Call training simulator",
     "text": "Staff rehearse your five hardest calls — the 2am emergency to the furious repeat customer — scored, before touching a real line."},
    {"icon": "📝", "title": "Recordings + notes",
     "text": "Every call recorded (announced), transcribed, and filed. Play it back, search it, learn from it."},
    {"icon": "⭐", "title": "Review engine",
     "text": "Happy callers get nudged to Google at the right moment. Phone-complaint reviews dry up at the source."},
    {"icon": "💬", "title": "WhatsApp + Meta agent, wired to us",
     "text": "We configure Meta's free agent on your WhatsApp for FAQs and bookings. Anything warm, urgent, or human goes to us by handoff — days and nights covered."},
]

PROOF = [
    {"stat": "64.3%", "text": "of weekend plumbing calls were qualified leads — the best calls come out of hours (Kept, 1,394 real calls)"},
    {"stat": "49.1% vs 37.4%", "text": "after-hours vs daytime lead qualification. Nights beat days."},
    {"stat": "1 in 8", "text": "trade Google reviews cite phone unreachability — #1 gripe is no callback (11,500 reviews)"},
    {"stat": "93.3%", "text": "of bad electrician reviews are process failure, not wiring (1,271 reviews)"},
]


def _clean(text: str, biz: str) -> str:
    """Swap [BRACKET] onboarding placeholders for display-safe defaults."""
    subs = {
        "SERVICE AREA": "your area",
        "BUSINESS NAME": biz, "SHOP NAME": biz, "SALON NAME": biz,
        "OWNER FIRST NAME": "the owner", "OWNER": "the owner",
        "WORK NUMBER": "your work number", "OWNER MOBILE": "your mobile",
        "EMAIL FOR MORNING DIGEST": "your inbox",
        "MORNING DIGEST": "morning digest",
        "EMAIL": "your inbox", "WHATSAPP NUMBER": "your WhatsApp",
        "WHATSAPP": "WhatsApp",
        "RATE BANDS": "published rates", "MENU RANGES": "published rates",
        "PRICE LIST RANGES": "published rates", "RATE CARD RANGES": "published rates",
        "RATE CARD": "rate card",
        "DEPOSIT POLICY": "a fair deposit policy", "NO-SHOW POLICY": "a fair no-show policy",
        "POLICY": "the house policy",
        "TRADE": "trade", "TRADE RATE BANDS": "published rates",
        "TRADE EMERGENCY RULE": "the trade emergency rule",
        "TRADE-SPECIFIC": "trade-specific",
        "HOW WAIT IS TRACKED": "live shop state",
        "STANDARD JOB TYPES": "standard jobs",
        "WHAT COUNTS AS URGENT IN THIS TRADE": "genuine urgencies",
    }

    def rep(m):
        return subs.get(m.group(1).strip(), "")

    out = re.sub(r"\[([^\]]+)\]", rep, text or "")
    return re.sub(r"\s{2,}", " ", out).strip()


def load_pack(filename: str) -> dict:
    with open(os.path.join(KNOWLEDGE, filename), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def industries() -> dict:
    out = []
    for t in TRADES:
        try:
            pack = load_pack(t["file"])
        except OSError:
            continue
        nodes = pack.get("nodes", []) or []
        biz = str((pack.get("business", {}) or {}).get("name", ""))
        if not biz or "[" in biz or "{" in biz:
            biz = t["label"].rstrip("s")
        services = [{"id": n.get("id", ""), "name": n.get("name", ""),
                     "text": _clean(n.get("text", ""), biz)}
                    for n in nodes if n.get("type") == "service"]
        pricing = _clean(next((n.get("text", "") for n in nodes
                               if n.get("id") == "policy.pricing"), ""), biz)
        emergency = _clean(next((n.get("text", "") for n in nodes
                                 if "emergency" in (n.get("id", "") or "")), ""), biz)
        script = _clean((pack.get("launch", {}) or {}).get("v1_script", ""), biz)
        prompt = _clean(str((pack.get("agent", {}) or {}).get("system_prompt", ""))[:400], biz)
        hours = (pack.get("business", {}) or {}).get("hours", {}) or {}
        escal = [{"name": n.get("name", ""), "aliases": (n.get("aliases") or [])[:4]}
                 for n in nodes if n.get("type") == "escalation"]
        out.append({"slug": t["slug"], "label": t["label"], "icon": t["icon"],
                    "hours": {str(k): str(v) for k, v in hours.items()},
                    "escalations": escal,
                    "tagline": t["tagline"], "services": services,
                    "pricing": pricing, "emergency": emergency,
                    "script": script, "prompt": prompt})
    return {"industries": out, "core": CORE_SERVICES, "proof": PROOF,
            "price": "50p per active minute. No subscription. First 10 calls free."}
