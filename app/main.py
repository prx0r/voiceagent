from __future__ import annotations
import os, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import Settings
from .graph import KnowledgeGraph
from .store import Store
from .tools import ToolRegistry
from .llm import LLM
from . import cases as casekit
from . import session as livesession

settings = Settings()
business = Settings.load_business(settings.business_config)
case_store = casekit.CaseStore("runtime/cases")
graph = KnowledgeGraph(business)
store = Store(settings.support_db)
tools = ToolRegistry(business, store)
llm = LLM(settings)

app = FastAPI(title="Supplier Support Agent Kernel", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


def require_key(request: Request):
    """Per-sparky API keys. Unset SPARKY_API_KEYS = open (dev); set = enforced
    on sparky/intake actions. Homeowner funnel stays public by design."""
    allowed = [k.strip() for k in
               os.getenv("SPARKY_API_KEYS", "").split(",") if k.strip()]
    if not allowed:
        return
    got = (request.headers.get("X-VoltLine-Key", "")
           or request.query_params.get("key", ""))
    if got not in allowed:
        raise HTTPException(401, "bad or missing X-VoltLine-Key")

class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    locale: str | None = None
    speak: bool = False

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"ok": True, "business": business.get("business",{}).get("name"), "llm": llm.enabled, "nodes": len(graph.nodes)}

@app.post("/chat")
async def chat(inp: ChatIn):
    sid = inp.session_id or str(uuid.uuid4())
    store.add_message(sid, "user", inp.message, {"locale": inp.locale})
    context, evidence = graph.context(inp.message)
    hist = store.history(sid, 10)
    sys = business.get("agent",{}).get("system_prompt", "You are a precise customer support agent.")
    result = await llm.respond(sys, hist[:-1], inp.message, context, tools.descriptions())
    tool_result = None
    # Output guard FIRST: a jailbroken turn must not reach tools either.
    from .guard import enforce as _enforce
    _g = _enforce(result.get("answer", ""), sid)
    if _g != result.get("answer", ""):
        result["answer"] = _g
        result["tool"] = None
    if result.get("tool"):
        tool_result = tools.call(result["tool"], result.get("tool_args") or {}, sid)
        # Never pretend success. Second pass: the model summarizes the
        # MEASURED result, so it can't hallucinate numbers it wrote blind.
        if tool_result.get("ok"):
            if llm.enabled:
                summary = await llm.respond(
                    sys + " Reply in two sentences max. Quote measured values exactly.",
                    hist, inp.message,
                    f"Measured tool result (ground truth, quote exactly): {tool_result}",
                    {})
                result["answer"] = summary.get("answer", result.get("answer", ""))
            else:
                result["answer"] = result.get("answer", "") + f"\n\nAction result: {tool_result}"
        else:
            result["answer"] = result.get("answer", "") + "\n\nI couldn't complete that action; a human should take over."
    result["answer"] = _enforce(result.get("answer", ""), sid)
    store.add_message(sid, "assistant", result.get("answer", ""), {"evidence": evidence, "tool_result": tool_result})
    audio_url = None
    if inp.speak and result.get("answer"):
        try:
            from adapters.edge_tts import synthesize
            path = await synthesize(result["answer"], business.get("voice",{}).get("edge_voice", settings.edge_tts_voice))
            audio_url = "/tts/" + os.path.basename(path)
        except Exception as e:
            audio_url = None
    return {"session_id": sid, "answer": result.get("answer"), "evidence": evidence, "tool": result.get("tool"), "tool_result": tool_result, "confidence": result.get("confidence"), "audio_url": audio_url}

@app.get("/tts/{filename}")
def tts(filename: str):
    if "/" in filename or ".." in filename:
        raise HTTPException(400)
    path = Path("runtime/tts") / filename
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="audio/mpeg")

@app.get("/graph/search")
def graph_search(q: str):
    return [h.__dict__ for h in graph.search(q, 10)]


@app.get("/quote")
def quote_page():
    return FileResponse("static/quote.html")


@app.post("/funnel/qualify")
async def funnel_qualify(
    postcode: str = "",
    charger: str = "",
    three_phase: bool = False,
):
    """Step 1: JSON qualify (photos counted client-side, files via /funnel/upload).

    Kept JSON-first so the funnel works without multipart pain; photo
    presence is passed as flags. File upload is separate + optional.
    """
    from fastapi import Request as _Req  # lazy, no cycle
    return _qualify_payload({"postcode": postcode, "charger": charger,
                             "three_phase": three_phase})


def _qualify_payload(p: dict) -> dict:
    from . import evtools as _ev
    res = _ev.qualify_lead({
        "postcode": p.get("postcode", ""),
        "parking_photo": p.get("parking_photo", p.get("parking")),
        "consumer_unit_photo": p.get("consumer_unit_photo", p.get("consumer_unit")),
        "meter_photo": p.get("meter_photo", p.get("meter")),
        "charger_shortlist": p.get("charger", p.get("charger_shortlist", "")),
        "three_phase": p.get("three_phase", False),
    })
    return res


@app.post("/funnel/qualify_json")
async def funnel_qualify_json(payload: dict):
    return _qualify_payload(payload or {})


class FunnelBookIn(BaseModel):
    name: str = ""
    phone: str = ""
    postcode: str = ""
    slot: str = "next-available"
    charger: str = ""
    idempotency_key: str | None = None
    photos: dict = {}


@app.post("/funnel/book")
async def funnel_book(inp: FunnelBookIn):
    """Step 2: book survey + open case. Idempotent on idempotency_key."""
    from . import evtools as _ev
    key = inp.idempotency_key or str(uuid.uuid4())
    receipt = _ev.book_survey({"name": inp.name, "phone": inp.phone,
                               "postcode": inp.postcode, "slot": inp.slot,
                               "idempotency_key": key})
    if not receipt.get("ok"):
        raise HTTPException(400, receipt.get("error", "bad request"))
    if receipt.get("replayed"):
        return {**receipt, "idempotency_key": key}
    # Every booking becomes a case with photos attached — survives handoffs.
    case = casekit.new_case(inp.phone or inp.name, "ev-funnel")
    casekit.apply(case, {"type": "intent.set",
                         "payload": {"intent": "EV_SURVEY"}})
    casekit.apply(case, {"type": "observation.added",
                         "payload": {"otype": "funnel",
                                     "value": f"{inp.postcode} {inp.charger} {inp.slot}",
                                     "confidence": 1.0}})
    for label, ref in (inp.photos or {}).items():
        casekit.apply(case, {"type": "observation.added",
                             "payload": {"otype": f"photo:{label}",
                                         "value": str(ref)[:300],
                                         "confidence": 1.0}})
    casekit.apply(case, {"type": "action.taken",
                         "payload": {"tool": "book_survey",
                                     "receipt": receipt,
                                     "idempotency_key": key}})
    case_store.save(case)
    store.create_ticket(case["case_id"], "ev-survey",
                        {"booking": receipt, "charger": inp.charger})
    return {**receipt, "case_id": case["case_id"],
            "idempotency_key": key}


@app.post("/funnel/upload")
async def funnel_upload(file: UploadFile):
    """Optional photo store. Returns a ref to attach to /funnel/book.photos."""
    safe = "".join(c if c.isalnum() or c in "-_." else "_"
                   for c in (file.filename or "photo.jpg"))[:64] or "photo.jpg"
    dest = Path("runtime/uploads") / f"{uuid.uuid4().hex[:8]}_{safe}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "max 8MB per photo")
    dest.write_bytes(data)
    return {"ok": True, "ref": str(dest), "bytes": len(data)}


class CaseIn(BaseModel):
    customer_id: str = ""
    channel: str = "web"


@app.post("/cases")
async def case_open(inp: CaseIn):
    """Open a case + its LiveKit room. The room is best-effort until
    a server is configured; the case itself always works."""
    case = casekit.new_case(inp.customer_id, inp.channel)
    case_store.save(case)
    room = livesession.room_name(case["case_id"])
    live = await livesession.ensure_room(room)
    return {"case_id": case["case_id"], "room": room, "livekit": live}


@app.get("/cases/{case_id}")
def case_get(case_id: str):
    case = case_store.load(case_id)
    if not case:
        raise HTTPException(404)
    return case


class JoinIn(BaseModel):
    identity: str
    role: str = "caller"


@app.post("/cases/{case_id}/join")
def case_join(case_id: str, inp: JoinIn):
    if not case_store.load(case_id):
        raise HTTPException(404)
    try:
        return livesession.mint_token(inp.identity,
                                      livesession.room_name(case_id), inp.role)
    except RuntimeError as e:
        raise HTTPException(503, str(e))


class EventIn(BaseModel):
    type: str
    payload: dict = {}


@app.post("/cases/{case_id}/events")
def case_event(case_id: str, inp: EventIn):
    """Resolver/agents/humans feed the case here. Conversation is not state."""
    case = case_store.load(case_id)
    if not case:
        raise HTTPException(404)
    casekit.apply(case, {"type": inp.type, "payload": inp.payload})
    case_store.save(case)
    return {"ok": True, "events": len(case["events"])}


@app.get("/cases/{case_id}/brief")
def case_brief(case_id: str):
    return {"brief": case_store.brief(case_id)}


# ---- Sparky MVP: overnight intake -> morning digest -> one-click actions ----

def _profile() -> dict:
    from . import tradie as _t
    try:
        return _t.load_profile()
    except Exception:
        return {"tradie": {}, "preferences": {}, "prices": {},
                "calendar": {"file": "runtime/calendar.json"},
                "messages": {}}


class IntakeIn(BaseModel):
    transcript: str
    name: str = ""
    phone: str = ""
    postcode: str = ""
    channel: str = "voice"
    hour: int | None = None
    day: str | None = None   # YYYY-MM-DD for slot proposals
    charger: str = ""
    vulnerable: bool = False
    value_gbp: float = 300
    ease: str = "medium"
    parts: list = []
    parts_total: float = 0


@app.post("/calls/intake")
def calls_intake(inp: IntakeIn, request: Request):
    """Simulated inbound call/text. Real PSTN (Telnyx/LiveKit SIP) or WhatsApp
    webhook posts transcripts here; Qwen realtime feeds the same path."""
    require_key(request)
    from . import afterhours as _ah
    return _ah.intake_call(inp.transcript, inp.model_dump(), case_store,
                           _profile())


@app.get("/sparky")
def sparky_page():
    return FileResponse("static/sparky.html")


@app.get("/sparky/digest")
def sparky_digest():
    from . import afterhours as _ah
    return {"tradie": (_profile().get("tradie") or {}).get("name", "sparky"),
            "items": _ah.morning_digest(case_store, _profile())}


class ActIn(BaseModel):
    case_id: str = ""
    action: str = ""
    to: str = ""
    text: str = ""
    start: str = ""
    minutes: int = 90
    token: str = ""
    items: list = []
    job_type: str = ""


@app.post("/sparky/act")
def sparky_act(inp: ActIn, request: Request):
    """One-click actions from the morning queue. Approvals explicit, audited."""
    require_key(request)
    from . import tradie as _t
    from . import parts as _p
    from tools import calendar as _cal
    from tools import whatsapp as _wa
    prof = _profile()
    cal_path = (prof.get("calendar") or {}).get("file", "runtime/calendar.json")
    case = case_store.load(inp.case_id) if inp.case_id else None
    if inp.action == "book_slot":
        r = _cal.book(cal_path, f"Job {inp.case_id}", inp.start,
                      inp.minutes, getattr(inp, "postcode", ""))
        if r.get("ok") and case:
            casekit.apply(case, {"type": "action.taken",
                                 "payload": {"tool": "calendar.book",
                                             "receipt": r["event"],
                                             "idempotency_key": inp.start}})
            case_store.save(case)
        return r
    if inp.action == "send_response":
        if not inp.to:
            raise HTTPException(400, "to required")
        r = _wa.send(inp.to, inp.text or "Hi — Dan here, replying to your enquiry.")
        if case:
            casekit.apply(case, {"type": "action.taken",
                                 "payload": {"tool": "whatsapp.send",
                                             "receipt": {"to": inp.to},
                                             "idempotency_key": inp.text[:32]}})
            case_store.save(case)
        return r
    if inp.action == "propose_parts":
        return _p.propose(inp.items, inp.case_id)
    if inp.action == "approve_parts":
        return _p.approve(inp.token)
    if inp.action == "log_job":
        return _t.log_job_time(inp.job_type or "general", inp.minutes,
                               inp.case_id)
    if inp.action == "close_case":
        if not case:
            raise HTTPException(404, "unknown case")
        casekit.apply(case, {"type": "problem.updated",
                             "payload": {"status": "closed"}})
        case_store.save(case)
        return {"ok": True, "case_id": inp.case_id, "status": "closed"}
    if inp.action == "setup_pack":
        from tools import meta as _meta
        return _meta.business_setup_pack(prof)
    raise HTTPException(400, f"unknown action: {inp.action}")


@app.get("/sparky/export")
def sparky_export(request: Request):
    """Accountant export: job-time records as CSV. Records, not advice —
    the sparky (or their accountant) does the actual tax return."""
    require_key(request)
    import csv
    import io
    import json as _json
    from pathlib import Path as _Path
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "job_type", "minutes", "case_id"])
    p = _Path("runtime/job_stats.jsonl")
    if p.exists():
        for line in p.read_text().splitlines():
            try:
                r = _json.loads(line)
                w.writerow([r.get("t", ""), r.get("job_type", ""),
                            r.get("minutes", ""), r.get("case", "")])
            except Exception:
                continue
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(buf.getvalue(), media_type="text/csv")


@app.get("/jobs/feed")
def jobs_feed():
    """Shared area feed, scored per-THIS-tradie (calendar fit + prefs).
    Same feed for every contractor; order differs — the Insta-algo bit."""
    import json
    from . import tradie as _t
    prof = _profile()
    try:
        feed = json.loads(Path("graphs/job_feed.json").read_text())["jobs"]
    except Exception:
        feed = []
    out = []
    for j in feed:
        w = _t.worth_it(prof, j)
        chk = None
        if j.get("parts"):
            from . import parts as _p
            chk = _p.check(j["parts"])
        out.append({**j, "worth": w["score"], "verdict": w["verdict"],
                    "reasons": w["reasons"], "drive_min": w["drive_min"],
                    "parts_total": (chk or {}).get("parts_total", 0)})
    out.sort(key=lambda j: j["worth"], reverse=True)
    return {"jobs": out}
