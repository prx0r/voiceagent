"""Answered console: the guide agent, the read-only demo calendar and sourced stats.

See docs/CONSOLE_SPEC.md. Nothing here writes anywhere: the calendar is generated
deterministically per trade and day, and the guide only answers and suggests.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import random
import re
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ = ZoneInfo("Europe/London")

# ---------------------------------------------------------------- trade briefs
# What the owner cares about, what wakes them up, and the two calls to role-play.
BRIEF = {
    "electrician": dict(
        who="electricians", pain="sparking sockets and tripping boards at night, plus EV charger and EICR enquiries you can't quote from a ladder",
        emergency="My sockets are sparking and there's a burning smell", booking="Can someone come tomorrow to look at my fuse box? It keeps tripping",
        price_q="How much for an EV charger?", hours=("08:00", "17:30"), slot=60,
        jobs=["EICR", "Fault finding", "Consumer unit swap", "EV charger survey", "Socket install", "Lighting rewire"]),
    "plumber": dict(
        who="plumbers", pain="burst pipes and leaks at 2am, and quote requests that ring while you're under a sink",
        emergency="A pipe's burst under my sink and there's water everywhere", booking="My tap's dripping, can you come later this week?",
        price_q="How much to fit a new tap?", hours=("08:00", "17:30"), slot=60,
        jobs=["Leak repair", "Tap replacement", "Toilet repair", "Radiator valve", "Bathroom quote", "Blocked sink"]),
    "heating": dict(
        who="heating engineers", pain="no-heat calls on the first cold night and gas-smell panics that need the right advice instantly",
        emergency="No heating or hot water and I've got a newborn", booking="I need my annual boiler service, when's your next slot?",
        price_q="How much is a new combi boiler?", hours=("08:00", "17:30"), slot=90,
        jobs=["Boiler service", "Boiler repair", "Gas safety cert", "Power flush", "New boiler survey", "Radiator fit"]),
    "locksmith": dict(
        who="locksmiths", pain="lockouts at midnight where the first locksmith to answer gets the job",
        emergency="I'm locked out, my keys are inside and it's midnight", booking="Can you change my locks this week? We've just moved in",
        price_q="How much for an anti-snap lock?", hours=("08:00", "20:00"), slot=60,
        jobs=["Lockout", "Lock change", "Anti-snap upgrade", "uPVC mechanism", "Key cutting visit", "Security survey"]),
    "beauty": dict(
        who="salons", pain="booking calls mid-treatment, patch tests forgotten and no-shows that empty the chair",
        emergency="I've had a reaction to my lash tint and my eye is swollen", booking="Can I book gel nails for Friday afternoon?",
        price_q="How much is a lash lift?", hours=("09:30", "18:00"), slot=45,
        jobs=["Gel manicure", "Lash lift", "Brow lamination", "Facial", "Gel pedicure", "Patch test"]),
    "barber": dict(
        who="barbers", pain="the phone ringing while the clippers are running, and empty chairs from no-shows",
        emergency="I booked a fade for 3pm but can't make it, can I move it?", booking="Any slots this afternoon for a skin fade?",
        price_q="How much is a skin fade?", hours=("09:00", "18:30"), slot=30,
        jobs=["Skin fade", "Scissor cut", "Beard trim", "Fade and beard", "Kids cut", "Hot towel shave"]),
    "dogwalker": dict(
        who="dog walkers", pain="calls with six leads in your hand, and new clients who won't wait for a callback",
        emergency="My dog's been hurt on today's walk, what happened?", booking="Can you walk my dog tomorrow at noon?",
        price_q="How much is a weekly walk?", hours=("08:00", "18:00"), slot=60,
        jobs=["Group walk", "Solo walk", "Puppy visit", "Meet and greet", "Drop-in visit", "Home boarding check-in"]),
    "msp": dict(
        who="IT support teams", pain="P1 outages at 7am, phishing panics, and tier-1 tickets that bury your engineers",
        emergency="The whole office is offline and nobody can work", booking="We need a new starter set up for Monday",
        price_q="How much is managed IT per user?", hours=("08:30", "17:30"), slot=60,
        jobs=["Remote support", "New starter setup", "On-site visit", "M365 migration", "Firewall review", "Laptop rollout"]),
    "soletrader": dict(
        who="sole traders", pain="missing calls while you're on a job, and quote requests that go to whoever answers first",
        emergency="It's urgent, can someone come tonight?", booking="Can I book a quote visit for next week?",
        price_q="What do you charge for a callout?", hours=("08:00", "17:30"), slot=60,
        jobs=["Quote visit", "Repair job", "Install", "Follow-up visit", "Survey", "Small job"]),
}

NAMES = ["Sarah K", "Tom R", "Priya S", "James O", "Leah M", "Chris D", "Aisha B", "Mark T", "Jen W",
         "Dan H", "Grace L", "Omar F", "Ellie P", "Sam N", "Ruth C", "Ben A"]
AREAS = ["M20", "M14", "M21", "M16", "M19", "M33", "SK4", "M15", "M8", "SK8"]


def brief(slug: str) -> dict:
    return BRIEF.get(slug) or BRIEF["soletrader"]


# ---------------------------------------------------------------- calendar
def _hm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _fmt(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def calendar(slug: str, days: int = 5, now: dt.datetime | None = None) -> dict:
    """Read-only demo diary: next `days` working days, seeded by trade and date."""
    b = brief(slug)
    now = now or dt.datetime.now(TZ)
    open_m, close_m, slot = _hm(b["hours"][0]), _hm(b["hours"][1]), b["slot"]
    out, d = [], now.date()
    while len(out) < days:
        if d.weekday() != 6:  # closed Sundays
            rng = random.Random(f"{slug}:{d.isoformat()}")
            close = close_m if d.weekday() < 5 else min(close_m, _hm("14:00"))
            events, free, t = [], [], open_m
            while t + slot <= close:
                past = d == now.date() and t <= now.hour * 60 + now.minute
                if rng.random() < 0.55:
                    events.append({"start": _fmt(t), "end": _fmt(t + slot), "title": rng.choice(b["jobs"]),
                                   "customer": rng.choice(NAMES), "area": rng.choice(AREAS), "status": "booked"})
                elif not past:
                    free.append(_fmt(t))
                t += slot
            label = "Today" if d == now.date() else ("Tomorrow" if d == now.date() + dt.timedelta(days=1) else d.strftime("%a %-d %b"))
            out.append({"date": d.isoformat(), "label": label, "events": events, "free": free})
        d += dt.timedelta(days=1)
    return {"tz": "Europe/London", "read_only": True, "slot_minutes": slot, "days": out}


def next_free(slug: str, n: int = 3, after_today: bool = False) -> list[tuple[str, str]]:
    res = []
    for day in calendar(slug)["days"]:
        if after_today and day["label"] == "Today":
            continue
        for f in day["free"]:
            res.append((day["label"], f))
            if len(res) >= n:
                return res
    return res


def slots_sentence(slug: str, message: str = "") -> str:
    tom = bool(re.search(r"(?i)\btomorrow\b", message))
    m = message.lower()
    rng = (12, 17) if "afternoon" in m else (0, 12) if "morning" in m else (17, 24) if re.search(r"evening|after work|tonight", m) else None
    picks = next_free(slug, 30, after_today=tom)
    if rng:
        picks = [p for p in picks if rng[0] <= int(p[1][:2]) < rng[1]] or picks
    picks = picks[:3]
    if tom:
        picks = [p for p in picks if p[0] == "Tomorrow"] or picks
    if not picks:
        return "The diary's full this week, so I'll ask the owner to fit you in and ring you back."
    def lab(p):
        return f"{p[0].lower() if p[0] in ('Today', 'Tomorrow') else p[0]} at {p[1]}"
    parts = [lab(p) for p in picks]
    joined = ", ".join(parts[:-1]) + f" or {parts[-1]}" if len(parts) > 1 else parts[0]
    if len(parts) == 1:
        return f"The next free slot is {joined}. Does that suit you? I'll hold it and the owner confirms by text."
    return f"The next free slots are {joined}. Which suits you? I'll hold it and the owner confirms by text."


def calendar_context(slug: str) -> str:
    c = calendar(slug, 3)
    lines = [f"{d['label']} ({d['date']}): booked {len(d['events'])}, free {', '.join(d['free'][:6]) or 'none'}" for d in c["days"]]
    return "READ-ONLY DIARY (offer these free slots; never claim a booking is confirmed):\n" + "\n".join(lines)


# ---------------------------------------------------------------- stats
def stats(slug: str) -> list[dict]:
    try:
        data = json.load(open(os.path.join(ROOT, "knowledge", "stats.json"), encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    trade = [s for s in data.get(slug, []) if s.get("url")]
    glob = [s for s in data.get("global", []) if s.get("url")]
    picked = trade[:2] + glob[: 3 - len(trade[:2])]
    return picked[:3]


# ---------------------------------------------------------------- guide agent
PRODUCT = """PRODUCT FACTS (only these; never invent others):
- Answered picks up calls the owner misses (after hours or on a job), in the owner's cloned voice, and says it's an AI assistant.
- It runs the trade's intake, gives published guide prices, offers free slots from the owner's diary (read-only), and holds them for the owner to confirm.
- Emergencies trigger an instant SMS and WhatsApp to the owner with name, address, number and the safety advice given. Everything else goes in a 7am email digest with transcripts.
- Callback reminders every 2 hours until each caller is marked done.
- Price: 50p per active minute, no subscription, first 10 calls free. Setup is a 20-minute call: voice clone, call divert code, test call.
- Basic plan (subscription, with tech support): an AI-readable website on their domain that ChatGPT and Google can read and quote, plus Google Business Profile setup and sync.
- Add-ons: WhatsApp agent; an agent-run inbox on their own domain (e.g. hello@markelectrician.co.uk) that answers within policy and drafts the rest for approval; calendar sync that reads free/busy only and writes holds to a separate calendar, so personal details never leak; review nudges; lead tracking.
- Subscription and add-on prices are set on the setup call; never quote a figure for them.
- Also: a call-training simulator for staff, and recordings and notes."""


def guide_prompt(slug: str, business: str) -> str:
    b = brief(slug)
    st = "; ".join(f"{s['stat']} {s['text']} ({s['source']})" for s in stats(slug))
    return (f"You are Answered's product guide, talking to the owner of a UK {b['who'][:-1]} business, shown here as the sample "
            f"business {business}. Their pain: {b['pain']}. Be brief (two to three sentences), warm and concrete, in British English. "
            "Always end by steering to exactly one next step the owner can click: role-play a customer, take a live call, look at the "
            "diary, see what lands on their phone, check the cost, or set it up. Never invent statistics, prices or features.\n"
            f"{PRODUCT}\nSOURCED STATS YOU MAY QUOTE: {st or 'none'}")


def receptionist_prompt(cfg_prompt: str) -> str:
    return cfg_prompt


def _chip(label, kind, text=""):
    return {"label": label, "kind": kind, "text": text or label}


def funnel(slug: str, done: set[str]) -> list[dict]:
    b = brief(slug)
    steps = [
        ("emergency", _chip(f"Be my customer: \u201c{b['emergency']}\u201d", "roleplay", b["emergency"])),
        ("booking", _chip(f"Be my customer: \u201c{b['booking']}\u201d", "roleplay", b["booking"])),
        ("call", _chip("Ring it live with my voice", "call")),
        ("phone", _chip("What lands on my phone?", "panel", "phone")),
        ("calendar", _chip("How does it use my diary?", "panel", "calendar")),
        ("cost", _chip("What would it cost me?", "guide", "What would it cost me?")),
        ("site", _chip("Show me what my customers see", "panel", "website")),
        ("plans", _chip("What else comes with it? Website, Google, WhatsApp, email", "panel", "plans")),
        ("prompt", _chip("Show me its instructions for my trade", "guide", "Show me the system prompt")),
        ("setup", _chip("Set it up for me", "signup")),
    ]
    out = [c for k, c in steps if k not in done and k != "setup"][:3]
    return out + [steps[-1][1]]


def opening(slug: str, business: str) -> str:
    b = brief(slug)
    return (f"This is {business}, a sample {b['who'][:-1].replace(' team', '')} business running Answered. "
            f"It answers the calls you miss: {b['pain']}. Pick one below and you'll hear it handle a real call in about ten seconds.")


INTENTS = [
    ("plans", r"else|website|google|whatsapp|email|inbox|plan|add.?on|subscription|package"),
    ("cost", r"cost|price|pay|charge|how much|expensive|minute"),
    ("prompt", r"system prompt|instructions|prompt|how does it know|trained"),
    ("calendar", r"calendar|diary|slot|availability|book"),
    ("phone", r"phone|alert|text|sms|whatsapp|digest|notif|lands"),
    ("call", r"\bcall\b|ring|voice|live|hear"),
    ("setup", r"set ?up|start|sign|onboard|get started|divert"),
    ("site", r"customers see"),
    ("emergency", r"emergenc|urgent|2am|night"),
]


def guide_answer(slug: str, business: str, message: str, done: set[str], minutes_calc=None) -> dict:
    """Rule-based guide (used when no LLM, and to choose chips either way)."""
    b = brief(slug)
    intent = next((k for k, rx in INTENTS if re.search(rx, message, re.I)), "general")
    panel = None
    if intent == "cost":
        ans = ("50p per active minute, no subscription, and the first 10 calls are free. Forty missed calls a month at two minutes each "
               "comes to £30. One job won back covers that several times over.")
    elif intent == "plans":
        ans = ("Answering is pay as you go. Basic adds a website that ChatGPT and Google can read and quote, your Google profile kept in sync, and "
               "tech support. On top: a WhatsApp agent, an agent-run inbox on your own domain, and diary sync that only sees busy or free, never your personal details.")
        panel = "plans"
    elif intent == "prompt":
        ans = (f"Every trade gets its own instructions. For {b['who']} it knows the emergencies, the safety advice to give, your guide prices, "
               "your hours and your diary, and it never confirms anything you haven't. The full prompt is open on screen.")
        panel = "prompt"
    elif intent == "calendar":
        f = next_free(slug, 2)
        when = " and ".join(f"{d} {t}" for d, t in f) if f else "the next free gaps"
        ans = (f"It reads your diary but never writes to it. Ask it for a visit and it offers real gaps, like {when}, "
               "holds one, and you confirm with a tap. Your demo diary is open on screen.")
        panel = "calendar"
    elif intent == "phone":
        ans = ("Emergencies text and WhatsApp you instantly with name, address, number and the advice given. Everything else lands "
               "in a 7am digest, and callback reminders nag every two hours until you've rung back.")
        panel = "phone"
    elif intent == "call":
        ans = "Press Call and talk to it like a customer would. It answers as the business, in a British voice, and you can hang up any time."
    elif intent == "setup":
        ans = ("Setup is a 20-minute call: we clone your voice, load your prices and hours, set your phone's divert code and test-ring it "
               "with you. Leave your number and we'll ring you.")
        panel = "signup"
    elif intent == "site":
        ans = "That's the site your customers get, built from your trade's playbook, with the same receptionist behind its chat."
        panel = "website"
    elif intent == "emergency":
        ans = f"Try it: be the customer with \u201c{b['emergency']}\u201d. It gives safety advice first, then texts you straight away."
    else:
        ans = f"Happy to show you. The fastest way to judge it is to be one of your own customers. Try \u201c{b['emergency']}\u201d."
    done = set(done) | ({intent} if intent != "general" else set())
    return {"answer": ans, "intent": intent, "panel": panel, "prompts": funnel(slug, done)}
