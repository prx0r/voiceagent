"""SupportCase: the conversation is NOT the state.

A case survives interruptions, model changes, phone->browser moves,
human escalation, callbacks tomorrow, and other agents. Every mutation
is an appended event — the case is the fold of its log.
"""
from __future__ import annotations
import json
import time
import uuid
from pathlib import Path


def new_case(customer_id: str = "", channel: str = "web") -> dict:
    now = time.time()
    return {
        "case_id": f"case_{uuid.uuid4().hex[:8]}",
        "customer": {"id": customer_id, "verified": False},
        "channel": channel,
        "intent": "",
        "problem": {"description": "", "status": "open"},
        "observations": [],
        "entities": [],
        "verified_facts": [],
        "actions": [],
        "next_required": "",
        "escalation": {"required": False, "reason": ""},
        "events": [{"t": now, "type": "case.opened", "channel": channel}],
        "created_at": now,
        "updated_at": now,
    }


def apply(case: dict, event: dict) -> dict:
    """Fold one event into the case. Pure-ish: mutates and returns it."""
    event = {"t": time.time(), **event}
    case["events"].append(event)
    case["updated_at"] = event["t"]
    typ = event.get("type", "")
    p = event.get("payload", {}) or {}
    if typ == "intent.set":
        case["intent"] = str(p.get("intent", ""))[:64]
    elif typ == "observation.added":
        case["observations"].append({
            "type": str(p.get("otype", "text"))[:32],
            "value": str(p.get("value", ""))[:500],
            "confidence": float(p.get("confidence", 0.5))})
    elif typ == "entity.candidate":
        case["entities"].append({"id": str(p.get("id", ""))[:64],
                                 "status": "candidate"})
    elif typ == "fact.verified":
        case["verified_facts"].append({"fact": str(p.get("fact", ""))[:300],
                                       "source": str(p.get("source", ""))[:64]})
    elif typ == "action.taken":
        case["actions"].append({"tool": str(p.get("tool", ""))[:64],
                                "receipt": p.get("receipt", {}),
                                "idempotency_key": str(p.get("idempotency_key", ""))})
    elif typ == "escalation.requested":
        case["escalation"] = {"required": True,
                              "reason": str(p.get("reason", ""))[:300]}
    elif typ == "problem.updated":
        case["problem"].update({k: str(v)[:500] for k, v in p.items()
                                if k in ("description", "status")})
    elif typ == "handoff.note":
        case["observations"].append({"type": "handoff",
                                     "value": str(p.get("note", ""))[:500],
                                     "confidence": 1.0})
    return case


class CaseStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def _file(self, case_id: str) -> Path:
        safe = "".join(c for c in case_id if c.isalnum() or c in "_-")[:32]
        return self.path / f"{safe}.json"

    def save(self, case: dict):
        self._file(case["case_id"]).write_text(json.dumps(case, indent=1))

    def load(self, case_id: str) -> dict | None:
        f = self._file(case_id)
        return json.loads(f.read_text()) if f.exists() else None

    def brief(self, case_id: str) -> str:
        """Warm-transfer briefing: a human reads this, never the raw log."""
        c = self.load(case_id)
        if not c:
            return "unknown case"
        lines = [f"Case: {c['case_id']}",
                 f"Problem: {c['problem'].get('description', '?')} "
                 f"({c['problem'].get('status', '?')})"]
        for f_ in c["verified_facts"]:
            lines.append(f"✓ {f_['fact']} [{f_['source']}]")
        for o in c["observations"]:
            if o["type"] != "handoff":
                lines.append(f"· saw: {o['value']} ({o['confidence']:.0%})")
        for a in c["actions"]:
            lines.append(f"· did: {a['tool']} → {a['receipt']}")
        if c["escalation"]["required"]:
            lines.append(f"ESCALATED: {c['escalation']['reason']}")
        if c["next_required"]:
            lines.append(f"Next: {c['next_required']}")
        return "\n".join(lines)
