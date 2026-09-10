#!/usr/bin/env python3
"""Night-shift simulation: 8 fresh recorded calls for our sparky, Dan.

Scenarios distilled from real sparky guidance (SparkPro, Blue Heron, O'Neill,
NICEIC, Corley, Henderson EV, Derby fault-finding — see docs/competitors + web
research 2026-09-10). Each states the EXPECTED triage; the report shows hits and
misses. Run: python3 scripts/simulate_calls.py  (uses in-process TestClient).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SCENARIOS = [
    {"id": "fishy-burning-2am",
     "transcript": ("It's 2am and there's a weird fishy burning plastic smell coming "
                    "from the cupboard where the fuse box is. No smoke I can see."),
     "meta": {"name": "Priya", "phone": "+447700900101", "postcode": "E2 9AA",
              "hour": 2, "day": "2026-09-11", "channel": "voice"},
     "expect": "wake_now",
     "why": "Blue Heron: fishy/burning plastic = thermoset melting, smouldering risk."},
    {"id": "dead-car-hospital-shift",
     "transcript": ("My charger just stopped, car is dead and I'm on a hospital shift "
                    "at 6am, I have to get there, please help."),
     "meta": {"name": "Sam", "phone": "+447700900102", "postcode": "E2 9AA",
              "hour": 23, "day": "2026-09-11", "channel": "voice",
              "vulnerable": True},
     "expect": "wake_now",
     "why": "Total loss of charge + vulnerable worker = wake per policy."},
    {"id": "breaker-trips-no-heat",
     "transcript": ("Every time I plug the car in the breaker trips. No smell, nothing "
                    "hot, just clicks off. I've left it off."),
     "meta": {"name": "Jo", "phone": "+447700900103", "postcode": "E2 9AA",
              "hour": 1, "day": "2026-09-11", "channel": "voice"},
     "expect": "routine",
     "why": "Henderson rule: breaker left OFF with no heat/smell = safe till morning."},
    {"id": "ohme-quote-driveway",
     "transcript": ("Hi do you fit Ohme chargers? Got a driveway in E2, what would it "
                    "cost roughly?"),
     "meta": {"name": "Alex", "phone": "+447700900104", "postcode": "E2 8AA",
              "hour": 21, "day": "2026-09-11", "channel": "voice",
              "charger": "Ohme"},
     "expect": "routine",
     "why": "Sales enquiry → qualify path, morning slots, range quote."},
    {"id": "scorched-plug",
     "transcript": ("The plug on my charger cable looks brown and scorched and the socket "
                    "feels hot. I'm scared to touch it."),
     "meta": {"name": "Ruth", "phone": "+447700900105", "postcode": "E5 8AB",
              "hour": 0, "day": "2026-09-11", "channel": "voice"},
     "expect": "wake_now",
     "why": "CarBuzz red status: scorch + heat = stop, same-day emergency."},
    {"id": "buzzing-fusebox",
     "transcript": ("There's a loud buzzing and crackling coming from the fuse box, "
                    "it's getting louder."),
     "meta": {"name": "Mo", "phone": "+447700900106", "postcode": "E8 3AA",
              "hour": 3, "day": "2026-09-11", "channel": "voice"},
     "expect": "wake_now",
     "why": "NICEIC/Corley: buzzing/crackling = arcing. (This one FAILED before the fix.)"},
    {"id": "workshop-22kw",
     "transcript": ("I run a small workshop, want a 22 kilowatt three phase charger, "
                    "what's the price?"),
     "meta": {"name": "Dev", "phone": "+447700900107", "postcode": "RM13 8AA",
              "hour": 20, "day": "2026-09-11", "channel": "voice",
              "charger": "three-phase"},
     "expect": "routine",
     "why": "Three-phase → DNO/engineer path, never a same-night promise."},
    {"id": "wont-start-maybe-schedule",
     "transcript": ("Charger won't start at all, no lights on it. Worked fine yesterday. "
                    "Oh and my Octopus schedule changed this week I think."),
     "meta": {"name": "Lee", "phone": "+447700900108", "postcode": "E2 9AA",
              "hour": 22, "day": "2026-09-11", "channel": "voice"},
     "expect": "routine",
     "why": "Mission Green: most 'dead charger' = schedules/settings. Free checks first."},
]


def main() -> int:
    from fastapi.testclient import TestClient
    import app.main as m
    c = TestClient(m.app)
    hits = 0
    print(f"{'SCENARIO':22} {'EXPECT':10} {'GOT':10} {'WAKE':6} WORTH  DRAFT")
    for s in SCENARIOS:
        r = c.post("/calls/intake", json={"transcript": s["transcript"],
                                          **s["meta"]})
        assert r.status_code == 200, r.text
        j = r.json()
        ok = j["level"] == s["expect"]
        hits += ok
        flag = "HIT " if ok else "MISS"
        w = j["worth_it"]
        print(f"{flag} {s['id']:22} {s['expect']:10} {j['level']:10} "
              f"{str(j['wake']['wake']):6} {w['score']:3} ({w['verdict']})")
        print(f"     draft: {j['draft_response'][:130]}")
        if not ok:
            print(f"     NOTE: {s['why']}")
    d = c.get("/sparky/digest").json()["items"]
    woke = sum(1 for i in d if i["escalated"])
    print(f"\n{len(SCENARIOS)} calls in, {hits} triaged as expected. "
          f"Digest holds {len(d)} cases, {woke} escalated.")
    print("Dan's morning: urgent first, rest queued with slots + drafts.")
    return 0 if hits == len(SCENARIOS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
