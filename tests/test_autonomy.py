import json
import os
import time
from types import SimpleNamespace

from app.llm import LLM, resolve_endpoint
from app import retention as R
from app.afterhours import format_transcript
from app import parts as P
from app.cases import CaseStore


def _s(**kw):
    d = {"llm_provider": "auto", "llm_base_url": "", "llm_api_key": "",
         "llm_model": ""}
    d.update(kw)
    return SimpleNamespace(**d)


def test_llm_provider_presets():
    assert resolve_endpoint(_s()) == ""
    assert LLM(_s()).enabled is False
    m = _s(llm_provider="meta", llm_api_key="k", llm_model="muse-spark-1.1")
    assert resolve_endpoint(m) == "https://api.meta.ai/v1/chat/completions"
    assert LLM(m).enabled is True
    o = _s(llm_provider="openai", llm_api_key="k", llm_model="gpt-x")
    assert resolve_endpoint(o).startswith("https://api.openai.com/v1")
    # explicit base wins over preset
    c = _s(llm_provider="meta", llm_base_url="https://myhost:8000/v1",
           llm_api_key="k", llm_model="m")
    assert resolve_endpoint(c) == "https://myhost:8000/v1/chat/completions"


def test_format_transcript_canonical():
    t = format_transcript("  fuse box sparking  ", {"name": "Jo", "channel": "voice"})
    assert "Jo" in t and "fuse box sparking" in t and "voice" in t


def test_parts_mcp_falls_back_to_table():
    assert P.SUPPLIER_MCP_URL == ""  # no env in tests
    assert P.mcp_lookup("ohme_home_pro") is None
    chk = P.check([{"sku": "ohme_home_pro", "qty": 1}])
    assert chk["ok"] and chk["parts_total"] == 549


def test_retention_keeps_open_sweeps_closed(tmp_path):
    store = CaseStore(str(tmp_path / "runtime" / "cases"))
    from app import cases as C
    open_c = C.new_case("111", "voice")
    store.save(open_c)
    closed_c = C.new_case("222", "voice")
    C.apply(closed_c, {"type": "problem.updated",
                       "payload": {"status": "closed"}})
    store.save(closed_c)
    # age the closed file beyond TTL
    f = store._file(closed_c["case_id"])
    old = time.time() - 200 * 86400
    os.utime(f, (old, old))
    rep = R.sweep(str(tmp_path), apply=False,
                  policy={**R.POLICY, "cases": 90 * 86400,
                          "escalated_extra": 90 * 86400})
    assert any(closed_c["case_id"] in s for s in rep["swept"])
    assert rep["kept"] >= 1  # open kept
    rep2 = R.sweep(str(tmp_path), apply=True,
                   policy={**R.POLICY, "cases": 90 * 86400,
                           "escalated_extra": 90 * 86400})
    assert not store._file(closed_c["case_id"]).exists()
    assert store.load(open_c["case_id"]) is not None


def test_triage_negation_and_arcing():
    from app.evtools import triage_urgency as t
    assert t("nothing hot, no smell, breaker trips", hour=1)["level"] == "routine"
    assert t("no smoke but the socket is sparking", hour=1)["level"] == "wake_now"
    assert t("loud buzzing and crackling from the fuse box", hour=3)["level"] == "wake_now"
    assert t("it is not burning", hour=2)["level"] == "routine"


def test_triage_word_boundaries_no_substring_fires():
    from app.evtools import triage_urgency as t
    assert t("shot the window with a BB gun", hour=2)["level"] == "routine"
    assert t("send a couple of photos", hour=2)["level"] == "routine"
    assert t("socket feels hot", hour=2)["level"] == "wake_now"
    assert t("sparking outlet", hour=2)["level"] == "wake_now"


def test_api_key_gating_and_close_case(monkeypatch):
    monkeypatch.setenv("SPARKY_API_KEYS", "secret1")
    from fastapi.testclient import TestClient
    import app.main as m
    c = TestClient(m.app)
    assert c.post("/sparky/act", json={"action": "log_job"}).status_code == 401
    r = c.post("/calls/intake", json={"transcript": "test triage",
                                      "postcode": "E2 9AA", "hour": 23})
    assert r.status_code == 401
    h = {"X-VoltLine-Key": "secret1"}
    r2 = c.post("/calls/intake", json={"transcript": "test triage",
                                       "postcode": "E2 9AA", "hour": 23},
                headers=h)
    assert r2.status_code == 200
    cid = r2.json()["case_id"]
    closed = c.post("/sparky/act", json={"case_id": cid, "action": "close_case"},
                    headers=h)
    assert closed.json()["status"] == "closed"
