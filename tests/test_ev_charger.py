import yaml
from app.graph import KnowledgeGraph
from app import evtools
from app.tools import ToolRegistry


class Store:
    def create_ticket(self, *a):
        return "t1"


def ev_graph():
    cfg = yaml.safe_load(open("knowledge/ev_charger_install_en.yaml"))
    return KnowledgeGraph(cfg)


def test_ev_pricing_never_invents():
    g = ev_graph()
    hits = g.search("how much does installation cost exactly?")
    assert hits and hits[0].node_id == "policy.pricing"
    assert "£950" in hits[0].node["text"] or "range" in hits[0].node["text"].lower()


def test_ev_charger_retrieval():
    g = ev_graph()
    assert any(h.node_id == "product.ohme" for h in g.search("Octopus Intelligent Ohme tariff"))
    assert any(h.node_id == "product.zappi" for h in g.search("solar charger eco modes"))
    assert any(h.node_id == "service.survey" for h in g.search("can I get a charger at my house"))


def test_ev_safety_escalation():
    g = ev_graph()
    hits = g.search("burning smell from consumer unit sparking")
    ids = [h.node_id for h in hits]
    assert "escalation.safety" in ids


def test_qualify_lead_scores_and_missing():
    full = evtools.qualify_lead({"postcode": "E2 8AA", "parking_photo": 1,
                                 "consumer_unit_photo": 1, "meter_photo": 1,
                                 "charger_shortlist": "Ohme"})
    assert full["score"] >= 80 and full["ready_to_book"] is True
    thin = evtools.qualify_lead({"postcode": "E2 8AA"})
    assert thin["ready_to_book"] is False and "consumer unit photo" in " ".join(thin["missing"])
    three = evtools.qualify_lead({"postcode": "E2 8AA", "parking_photo": 1,
                                  "consumer_unit_photo": 1, "meter_photo": 1,
                                  "three_phase": True})
    assert three["ready_to_book"] is False and "DNO" in three["next"]


def test_triage_wake_vs_routine():
    assert evtools.triage_urgency("burning smell from charger", hour=2)["level"] == "wake_now"
    assert evtools.triage_urgency("charger not charging, car dead", hour=2)["level"] == "routine"
    assert evtools.triage_urgency("charger not charging, car dead", hour=2, vulnerable=True)["level"] == "wake_now"
    assert evtools.triage_urgency("do you install Ohme?", hour=14)["level"] == "routine"


def test_book_survey_idempotent_via_registry():
    t = ToolRegistry({}, Store())
    a = t.call("book_survey", {"name": "Jo", "phone": "07700", "postcode": "E2 8AA",
                               "idempotency_key": "k1"}, "s")
    b = t.call("book_survey", {"name": "Jo", "phone": "07700", "postcode": "E2 8AA",
                               "idempotency_key": "k1"}, "s")
    assert a["ok"] and b.get("replayed") is True
    assert a["booking_id"] == b["booking_id"]
    bad = t.call("book_survey", {"name": "", "phone": "", "postcode": ""}, "s")
    assert bad["ok"] is False
