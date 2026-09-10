from fastapi.testclient import TestClient


def _client():
    import app.main as m
    return TestClient(m.app)


def test_quote_page_serves():
    c = _client()
    r = c.get("/quote")
    assert r.status_code == 200 and "EV charger" in r.text


def test_funnel_qualify_json_scores():
    c = _client()
    r = c.post("/funnel/qualify_json", json={"postcode": "E2 8AA"})
    assert r.status_code == 200
    j = r.json()
    assert j["score"] < 80 and j["ready_to_book"] is False
    r2 = c.post("/funnel/qualify_json", json={
        "postcode": "E2 8AA", "charger": "Ohme",
        "parking_photo": 1, "consumer_unit_photo": 1, "meter_photo": 1})
    assert r2.json()["ready_to_book"] is True


def test_funnel_book_creates_case_and_idempotent():
    import uuid
    c = _client()
    key = "t-" + uuid.uuid4().hex[:8]
    payload = {"name": "Test Jo", "phone": "07700900000",
               "postcode": "E2 8AA", "slot": "saturday",
               "charger": "Ohme", "idempotency_key": key, "photos": {}}
    r1 = c.post("/funnel/book", json=payload)
    assert r1.status_code == 200, r1.text
    j1 = r1.json()
    assert j1["booking_id"].startswith("SURV-") and "case_id" in j1
    # case retrievable with funnel observations
    case = c.get(f"/cases/{j1['case_id']}")
    assert case.status_code == 200
    assert any("photo" in str(e).lower() or "funnel" in str(e).lower()
               for e in case.json()["events"])
    # retry same key replays (no new case needed, same booking)
    r2 = c.post("/funnel/book", json=payload)
    assert r2.json()["booking_id"] == j1["booking_id"]


def test_funnel_book_rejects_empty():
    c = _client()
    r = c.post("/funnel/book", json={"name": "", "phone": "", "postcode": ""})
    assert r.status_code == 400


def test_funnel_upload_roundtrip(tmp_path):
    c = _client()
    r = c.post("/funnel/upload", files={"file": ("cu.jpg", b"fakebytes", "image/jpeg")})
    assert r.status_code == 200 and r.json()["ok"] is True
