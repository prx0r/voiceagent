"""Meta Business Agent bridge: trade pack -> live WhatsApp agent.

Flow: eligibility -> onboarding -> business info + FAQs + skill ->
settings (handoff to us) -> agent_test proof. Every step returns dicts;
nothing raises on missing creds (409-style next steps). Writes go only
with confirm=True. Mirrors the stonedoorway bridge pattern.
"""
from __future__ import annotations
import json
import os
import urllib.request

API = "https://api.facebook.com"
APIV = "2.0.0"


def _conf() -> tuple[str, str]:
    return (os.getenv("META_SUAT", "").strip(),
            os.getenv("META_PHONE_ID", "").strip())


def _call(method: str, path: str, body: dict | None = None) -> dict:
    token, _ = _conf()
    if not token:
        return {"ok": False, "reason": "meta not configured",
                "next": "set META_SUAT + META_PHONE_ID (system user token, whatsapp_business_messaging)"}
    try:
        req = urllib.request.Request(
            API + path,
            data=json.dumps(body or {}).encode() if method != "GET" else None,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json",
                     "X-API-Version": APIV},
            method=method)
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"ok": True, "data": json.loads(r.read() or b"{}")}
    except Exception as e:
        return {"ok": False, "reason": f"meta api failed: {e}"[:200]}


def check_eligibility() -> dict:
    _, pid = _conf()
    if not pid:
        return {"ok": False, "reason": "META_PHONE_ID not set"}
    r = _call("GET", f"/{pid}/agent_eligibility")
    if not r.get("ok"):
        return r
    return {"ok": True, "eligible": bool(r["data"].get("is_eligible"))}


def onboard() -> dict:
    _, pid = _conf()
    return _call("POST", f"/{pid}/agent_onboarding", {})


def push_business_info(name: str, hours: str, area: str) -> dict:
    _, pid = _conf()
    return _call("POST", f"/{pid}/agent_config/business_info",
                 {"name": name, "hours": hours, "area": area})


def push_faqs(faqs: list) -> dict:
    """faqs: [{question, answer}]. Returns counts, stops on first error."""
    _, pid = _conf()
    done, errors = 0, []
    for f in faqs:
        r = _call("POST", f"/{pid}/agent_config/faq",
                  {"question": f["question"][:300], "answer": f["answer"][:1000]})
        if r.get("ok"):
            done += 1
        else:
            errors.append(r.get("reason", "?"))
            break
    return {"ok": not errors, "pushed": done, "errors": errors}


def push_skill(title: str, description: str, skill: str) -> dict:
    _, pid = _conf()
    return _call("POST", f"/{pid}/agent_config/skills",
                 {"title": title[:64], "description": description[:1024],
                  "skill": skill[:20000]})


def set_handoff(message: str) -> dict:
    _, pid = _conf()
    return _call("PUT", f"/{pid}/agent_config/settings",
                 {"handoff": {"enabled": True, "message": message[:200],
                              "message_selection": "CUSTOM"},
                  "followup": {"enabled": True,
                               "followup_interval_in_seconds": 900,
                               "message": "Still there? Reply and we'll pick this up."}})


def agent_test(text: str, conversation_id: str = "") -> dict:
    _, pid = _conf()
    body = {"user_msg": text[:1000]}
    if conversation_id:
        body["conversation_id"] = conversation_id
    return _call("POST", f"/{pid}/agent_test", body)


def pack_to_faqs(pack: dict) -> list:
    """Trade pack nodes -> Meta FAQ entries. Policies + services + faqs."""
    faqs = []
    for n in pack.get("nodes", []) or []:
        kind = n.get("type", "")
        if kind in ("policy", "service", "faq") and n.get("name") and n.get("text"):
            faqs.append({"question": f"What is your {n['name']} policy?"
                         if kind == "policy" else f"{n['name']}?",
                         "answer": n["text"][:1000]})
    return faqs


def pack_to_skill(pack: dict) -> dict:
    """Trade pack -> one consolidated skill (Meta warns against conflicting ones)."""
    biz = (pack.get("business", {}) or {}).get("name", "the business")
    esc = next((n.get("text", "") for n in pack.get("nodes", []) or []
                if n.get("id") == "policy.escalation"), "escalate urgent issues")
    return {
        "title": "trade-receptionist",
        "description": f"Applies to every customer message for {biz}. Greeting, intake, escalation.",
        "skill": (
            f"You are the WhatsApp receptionist for {biz}. Greet briefly, answer "
            f"from the FAQs only, never invent prices or policies. Collect name, "
            f"need, and urgency for anything actionable. Hand off to a human "
            f"immediately when: {esc} Or when the customer asks twice for a "
            f"person, reports damage/injury, disputes payment, or raises safety. "
            f"Always offer the human path plainly; deflecting it is a failure."),
    }


def full_onboard(pack: dict, handoff_message: str, confirm: bool = False) -> dict:
    """Eligibility -> onboard -> knowledge -> skill -> settings -> test.
    Writes need confirm=True. Returns a step-by-step receipt."""
    steps = []
    el = check_eligibility()
    steps.append({"step": "eligibility", **el})
    if not el.get("ok") or not el.get("eligible"):
        return {"ok": False, "steps": steps,
                "next": "number ineligible: check vertical/country/verification standing"}
    if not confirm:
        return {"ok": False, "steps": steps,
                "reason": "confirm:true required (creates live agent config)",
                "next": "re-run with confirm:true on the setup call"}
    ob = onboard()
    steps.append({"step": "onboard", **{k: v for k, v in ob.items() if k != "data"}})
    if not ob.get("ok"):
        return {"ok": False, "steps": steps}
    biz = pack.get("business", {}) or {}
    bi = push_business_info(biz.get("name", ""), json.dumps(biz.get("hours", {})),
                            biz.get("area", ""))
    steps.append({"step": "business_info", **bi})
    fq = push_faqs(pack_to_faqs(pack))
    steps.append({"step": "faqs", **fq})
    sk = pack_to_skill(pack)
    st = push_skill(sk["title"], sk["description"], sk["skill"])
    steps.append({"step": "skill", **st})
    ho = set_handoff(handoff_message)
    steps.append({"step": "handoff", **ho})
    te = agent_test("Hi, what are your opening hours?")
    steps.append({"step": "test", "ok": te.get("ok", False),
                  "reply": str(te.get("data", ""))[:300]})
    return {"ok": all(s.get("ok") for s in steps), "steps": steps}
