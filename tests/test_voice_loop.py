import importlib.util

import yaml

from app.cases import CaseStore
from app.graph import KnowledgeGraph
from app import afterhours as AH
from app import tradie as T
from mocks.pipeline import VoiceLoop


def _scenarios():
    spec = importlib.util.spec_from_file_location(
        "sim", "scripts/simulate_calls.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SCENARIOS


def _loop(tmp_path):
    store = CaseStore(str(tmp_path / "cases"))
    prof = T.load_profile("knowledge/tradie_profile.yaml")
    prof["calendar"]["file"] = str(tmp_path / "cal.json")
    graph = KnowledgeGraph(yaml.safe_load(open("knowledge/ev_charger_install_en.yaml")))

    def intake_fn(transcript, meta):
        return AH.intake_call(transcript, meta, store, prof)

    return VoiceLoop(graph, intake_fn), store


def test_voice_loop_all_scenarios(tmp_path):
    loop, _ = _loop(tmp_path)
    for s in _scenarios():
        rep = loop.turn(s["transcript"], dict(s["meta"], day="2026-09-11"))
        assert rep.tool_calls, s["id"]
        assert rep.tool_calls[0]["result"] == s["expect"], s["id"]
        assert rep.evidence, s["id"]  # every answer grounded in graph nodes
        assert rep.answer, s["id"]
    assert len(loop.audit) == len(_scenarios())


def test_voice_loop_speculation_and_barge_in(tmp_path):
    loop, _ = _loop(tmp_path)
    rep = loop.turn("do you fit Ohme chargers, I have a driveway in E2",
                    {"postcode": "E2 8AA", "hour": 21, "day": "2026-09-11"},
                    barge_in="actually is Saturday morning free instead?",
                    barge_at_chars=50)
    assert rep.speculated is True           # eager partial fired a run
    assert rep.barged_in is True            # interruption registered
    assert rep.text_spoken and rep.text_dropped  # playback accounting complete
    assert any(a["event"] == "barge-in" for a in loop.audit)
    assert rep.simulated_ms < 800           # model budget under human-feel line
