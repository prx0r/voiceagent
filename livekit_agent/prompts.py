"""System instructions builder for the Telnyx LiveKit voice agent. Pure — no livekit
import, so unit tests cover it. The agent is the mouth; the kernel decides.
"""
from __future__ import annotations


def system_instructions(profile: dict, graph_hint: str = "") -> str:
    t = (profile.get("tradie") or {})
    prefs = (profile.get("preferences") or {})
    prices = (profile.get("prices") or {})
    msgs = (profile.get("messages") or {})
    name = t.get("name", "the engineer")
    biz = t.get("business", "VoltLine Electrical")
    ev = prices.get("ev_7kw_standard", [950, 1400])
    return f"""You answer the phone for {biz} as {name}'s assistant, after hours.
VOICE RULES: two sentences max per turn. Plain words, no jargon. Warm, unhurried.
NEVER say prices as final — ranges only: standard 7kW install £{ev[0]:g}-£{ev[1]:g},
callout £{prices.get('callout_weekday', 65):g} weekdays. Final quote needs a survey.
FLOW: 1) safety first — burning/smoke/shock/sparking means stop, tell them to switch
off if safe, and use the urgent tool. 2) Otherwise capture: name, postcode, what they
need, best callback number. 3) Say {name} replies in the morning{( ' — mornings first' if prefs.get('mornings_first') else '')}.
Use tools for EVERYTHING factual: triage_urgency first, then qualify or book.
If tools fail, take a message (name + number + one-line need) and confirm it back.
Sign off: {msgs.get('signoff', '')}
GRAPH EVIDENCE (quote only this, never invent):
{graph_hint or '[none — say you will log it for the engineer]'}"""


def opening_greeting(profile: dict, hour: int = 23) -> str:
    t = (profile.get("tradie") or {})
    daypart = "evening" if hour >= 18 else "morning" if hour < 12 else "afternoon"
    return (f"Hi, you've reached {t.get('business', 'VoltLine Electrical')} — "
            f"{t.get('name', 'Dan')}'s assistant, good {daypart}. "
            f"Is anyone hurt, or is there burning, smoke or sparking?")
