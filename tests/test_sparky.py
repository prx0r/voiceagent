import json
from pathlib import Path

from adapters.qwen_omni import session_update_event, function_output_event
from app import tradie as T
from app import afterhours as AH
from app import parts as P
from app.cases import CaseStore
from tools import calendar as cal


def _prof():
    return T.load_profile("knowledge/tradie_profile.yaml")


def test_qwen_session_update_shape():
    ev = session_update_event("hi", tools=[{"type": "function", "function": {"name": "x"}}])
    assert ev["type"] == "session.update"
    s = ev["session"]
    assert s["modalities"] == ["text", "audio"]
    assert s["input_audio_format"] == "pcm" and s["output_audio_format"] == "pcm"
    assert s["turn_detection"]["type"] == "semantic_vad"
    assert "enable_search" not in str(ev)  # tools XOR search
    fo = function_output_event("call_1", "result")
    assert fo["item"]["type"] == "function_call_output"


def test_worth_it_ranks_local_good_over_far():
    p = _prof()
    near = T.worth_it(p, {"postcode": "E2 9AA", "summary": "Ohme install",
                          "value_gbp": 1150, "ease": "easy",
                          "slot_is_morning": True})
    far = T.worth_it(p, {"postcode": "RM13 8AA", "summary": "zappi + solar",
                         "value_gbp": 1400, "ease": "medium"})
    assert near["score"] > far["score"]
    assert near["verdict"] == "take it"


def test_quote_ranges_not_invented():
    p = _prof()
    q = T.draft_quote(p, {"summary": "Ohme install", "name": "Jo",
                          "proposed_slots": ["2026-09-11T08:00"]}, parts_total=100)
    assert q["range"][0] >= 950 and "Jo" in q["text"]


def test_afterhours_wake_vs_queue(tmp_path):
    store = CaseStore(str(tmp_path / "cases"))
    p = _prof()
    p["calendar"]["file"] = str(tmp_path / "cal.json")
    urgent = AH.intake_call("burning smell from consumer unit, sparking",
                            {"phone": "077", "hour": 2, "day": "2026-09-11",
                             "postcode": "E2 9AA"}, store, p)
    assert urgent["level"] == "wake_now" and urgent["wake"]["wake"] is True
    assert any(a["id"] == "call_back_now" for a in urgent["actions"])
    routine = AH.intake_call("hi, do you fit Ohme chargers?",
                             {"phone": "078", "hour": 23, "day": "2026-09-11",
                              "postcode": "E2 9AA", "name": "Sam"}, store, p)
    assert routine["wake"]["wake"] is False
    assert routine["proposed_slots"] and routine["draft_response"]
    assert routine["worth_it"]["score"] > 0
    digest = AH.morning_digest(store, p)
    assert len(digest) == 2 and digest[0]["escalated"] is True


def test_parts_approve_gated():
    chk = P.check([{"sku": "ohme_home_pro", "qty": 1}])
    assert chk["ok"] and chk["parts_total"] == 549
    prop = P.propose([{"sku": "ohme_home_pro", "qty": 1}], "case_x")
    assert prop["ok"] and prop["approval_token"].startswith("parts_")
    assert P.approve("bogus")["ok"] is False
    ok = P.approve(prop["approval_token"])
    assert ok["ok"] and ok["status"] == "ordered_pending_delivery"
    assert P.approve(prop["approval_token"])["ok"] is False  # single-use


def test_calendar_mornings_first_and_clash(tmp_path):
    path = str(tmp_path / "cal.json")
    assert cal.book(path, "Job A", "2026-09-11T08:00", 60)["ok"] is True
    assert cal.book(path, "Clash", "2026-09-11T08:30", 60)["ok"] is False
    slots = cal.free_slots(path, "2026-09-11", mornings_first=True)
    assert slots and int(slots[0][11:13]) < 12


def test_api_intake_digest_act_feed():
    from fastapi.testclient import TestClient
    import app.main as m
    c = TestClient(m.app)
    r = c.post("/calls/intake", json={"transcript": "Ohme install quote please",
                                      "name": "Api Tess", "phone": "079",
                                      "postcode": "E2 9AA", "hour": 23})
    assert r.status_code == 200 and r.json()["case_id"]
    d = c.get("/sparky/digest")
    assert d.status_code == 200 and d.json()["items"]
    f = c.get("/jobs/feed")
    jobs = f.json()["jobs"]
    assert jobs[0]["worth"] >= jobs[-1]["worth"]  # personalised order
    a = c.post("/sparky/act", json={"case_id": r.json()["case_id"],
                                    "action": "log_job", "job_type": "ev_charger",
                                    "minutes": 100})
    assert a.json()["ok"] is True
    assert T.avg_duration("ev_charger") and T.avg_duration("ev_charger") > 0
