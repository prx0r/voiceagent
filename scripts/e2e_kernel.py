#!/usr/bin/env python3
"""Kernel e2e: the whole sparky loop in one pass, asserted + logged.

qualify -> book -> urgent intake -> routine intake -> digest -> act
(book slot / send reply / close) -> feed -> export -> retention dry-run.
Run: python3 scripts/e2e_kernel.py | tee var/e2e_kernel.log
Exit non-zero on any failed assertion.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    from fastapi.testclient import TestClient
    import app.main as m
    c = TestClient(m.app)
    tag = uuid.uuid4().hex[:6]
    log = []

    def step(name, cond, detail=""):
        log.append(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
        assert cond, name

    step("health", c.get("/health").json()["ok"] is True)
    step("pages", c.get("/quote").status_code == 200 and c.get("/sparky").status_code == 200)

    q = c.post("/funnel/qualify_json", json={"postcode": "E2 8AA", "charger": "Ohme",
               "parking_photo": 1, "consumer_unit_photo": 1, "meter_photo": 1}).json()
    step("qualify-ready", q["ready_to_book"] is True, f"score={q['score']}")

    b = c.post("/funnel/book", json={"name": "E2E Tess", "phone": "07700900111",
               "postcode": "E2 8AA", "slot": "saturday", "charger": "Ohme",
               "idempotency_key": f"e2e-{tag}"}).json()
    step("book", b["booking_id"].startswith("SURV-"), b["booking_id"])
    b2 = c.post("/funnel/book", json={"name": "E2 E2E Tess", "phone": "07700900111",
                "postcode": "E2 8AA", "idempotency_key": f"e2e-{tag}"}).json()
    step("book-idempotent", b2.get("replayed") is True and b2["booking_id"] == b["booking_id"])

    u = c.post("/calls/intake", json={"transcript": "burning smell from the fuse box, sparking",
               "phone": "07700900222", "postcode": "E2 9AA", "hour": 2,
               "day": "2026-09-11"}).json()
    step("urgent-wakes", u["level"] == "wake_now" and u["wake"]["wake"] is True)
    r = c.post("/calls/intake", json={"transcript": "do you fit Ohme chargers?",
               "name": "Night Ned", "phone": "07700900333", "postcode": "E2 9AA",
               "hour": 23, "day": "2026-09-11", "charger": "Ohme"}).json()
    step("routine-queues", r["level"] == "routine" and not r["wake"]["wake"]
         and len(r["proposed_slots"]) > 0, f"worth={r['worth_it']['score']}")

    d = c.get("/sparky/digest").json()["items"]
    step("digest", len(d) >= 2 and d[0]["escalated"] is True, f"items={len(d)}")

    slot = r["proposed_slots"][0]
    bk = c.post("/sparky/act", json={"case_id": r["case_id"], "action": "book_slot",
                "start": "2026-09-12T08:00", "minutes": 90}).json()
    step("act-book", bk.get("ok") is True, f"slot={slot}")
    snd = c.post("/sparky/act", json={"case_id": r["case_id"], "action": "send_response",
                 "to": "07700900333", "text": "Morning — Dan here."}).json()
    step("act-send", snd.get("ok") is True, snd.get("queued", "live"))
    wise = c.post("/sparky/act", json={"case_id": r["case_id"], "action": "log_job",
                  "job_type": "ev_charger", "minutes": 95}).json()
    step("act-log", wise.get("ok") is True)
    cls = c.post("/sparky/act", json={"case_id": r["case_id"], "action": "close_case"}).json()
    step("act-close", cls.get("status") == "closed")

    f = c.get("/jobs/feed").json()["jobs"]
    step("feed-ranked", f[0]["worth"] >= f[-1]["worth"], f"top={f[0]['id']}:{f[0]['worth']}")
    ex = c.get("/sparky/export").text.strip().splitlines()
    step("export", len(ex) >= 2 and ex[0].startswith("timestamp"), f"rows={len(ex)-1}")

    from app.retention import sweep
    rep = sweep(".", apply=False)
    step("retention-dryrun", rep["kept"] >= 1, f"kept={rep['kept']} swept={len(rep['swept'])}")

    print("\n".join(log))
    print(f"\nE2E KERNEL: {len(log)}/{len(log)} steps green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
