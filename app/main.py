from __future__ import annotations
import os, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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

class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    locale: str | None = None
    speak: bool = False

@app.get("/")
def home():
    return FileResponse("static/grid.html")

@app.get("/kernel")
def kernel():
    return FileResponse("static/index.html")

@app.get("/grid")
def grid():
    return FileResponse("static/grid.html")

SAMPLE_BIZ = {
    "electrician": "Dave's Electrical", "plumber": "Flowright Plumbing",
    "heating": "CosyHeat", "locksmith": "Keyline Locks",
    "beauty": "Glow Studio", "barber": "Fade Factory",
    "dogwalker": "Happy Tails", "msp": "Nimbus IT",
}

@app.get("/demo/{trade}")
def demo_site(trade: str):
    """Live sample site per trade: what their customers see + what ships."""
    from . import industries as site_data
    slugs = [t["slug"] for t in site_data.TRADES]
    slug = trade if trade in slugs else "soletrader"
    meta = next(t for t in site_data.TRADES if t["slug"] == slug)
    biz = SAMPLE_BIZ.get(slug, "Sample & Sons")
    area = "Manchester"
    html = open("static/demo_template.html", encoding="utf-8").read()
    for k, v in {"BUSINESS": biz, "TRADE_LABEL": meta["label"],
                 "TRADE": slug, "ICON": meta["icon"],
                 "TAGLINE": meta["tagline"], "AREA": area,
                 "SLUG": slug}.items():
        html = html.replace("{{" + k + "}}", v)
    return HTMLResponse(html)

@app.get("/site")
def site():
    return FileResponse("static/site.html")

@app.get("/api/industries")
def api_industries():
    from . import industries as site_data
    return site_data.industries()

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
            if settings.tts_provider == "fish":
                from adapters.fish_tts import synthesize
                v = business.get("voice", {})
                path = await synthesize(
                    result["answer"],
                    v.get("fish_voice_id", "") or settings.edge_tts_voice,
                    model=v.get("fish_model", "s2.1-pro-free"))
            else:
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

class HandoffIn(BaseModel):
    customer_phone: str = ""
    to: str = ""
    metadata: str = ""
    summary: str = ""

@app.post("/webhooks/meta-handoff")
async def meta_handoff(inp: HandoffIn):
    """Meta Business Agent escalation receiver -> afterhours flow."""
    import meta_handoff as mh
    biz = business.get("business", {}) or {}
    return mh.handle_handover(
        {"customer_phone": inp.customer_phone, "to": inp.to,
         "metadata": inp.metadata, "summary": inp.summary},
        biz.get("digest_to", ""))

class BookIn(BaseModel):
    business: str = ""
    name: str = ""
    phone: str = ""
    email: str = ""
    service: str = ""
    when: str = ""
    date: str = ""
    time: str = ""

class CallbackIn(BaseModel):
    business: str = ""
    name: str = ""
    phone: str = ""
    reason: str = ""

@app.post("/api/callback")
async def api_callback(inp: CallbackIn):
    """'Call me back' shared function: ticket + nagging reminder."""
    if len(inp.name.strip()) < 2 or len(inp.phone.strip()) < 7:
        return {"ok": False, "reason": "name + valid callback number required"}
    tid = store.create_ticket(str(uuid.uuid4()), "callback", inp.model_dump())
    try:
        import sys as _s
        _s.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from afterhours import queue_reminder
        queue_reminder(inp.name.strip(), inp.phone.strip(),
                       f"call-me-back: {inp.reason.strip()[:200] or 'no reason given'}",
                       "standard", inp.business.strip())
    except Exception:
        pass
    return {"ok": True, "ticket_id": tid}

@app.get("/api/availability")
def api_availability():
    """Read-only availability: next days with free slots. Never writes."""
    import booking as booking_engine
    return {"ok": True, "days": booking_engine.propose()}

@app.post("/api/book")
async def api_book(inp: BookIn):
    """Propose -> confirm booking. No date yet? returns free slots to pick.
    Confirm path stores the row, queues the callback reminder, captures the
    customer email, and best-effort sends the confirmation email."""
    import booking as booking_engine
    if not inp.date or not inp.time:
        return {"ok": True, "needs_pick": True,
                "days": booking_engine.propose()}
    r = booking_engine.confirm(inp.business, inp.name, inp.phone, inp.email,
                               inp.service, inp.date, inp.time)
    if r.get("ok") and inp.email and "@" in inp.email:
        try:
            from adapters.gmail_notify import send_digest
            r["emailed"] = bool(send_digest(inp.email,
                        f"Booking confirmed: {r['date']} {r['time']} (ref {r['ref']})",
                        f"Hi {inp.name.strip()},\n\nYou're booked for {inp.service or 'the visit'} "
                        f"on {r['date']} at {r['time']} (ref {r['ref']}).\n"
                        f"We'll ring {inp.phone.strip()} if anything changes.\n\n— {inp.business.strip() or 'us'}").get("ok"))
        except Exception:
            r["emailed"] = False
    return r

@app.get("/graph/search")
def graph_search(q: str):
    return [h.__dict__ for h in graph.search(q, 10)]


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
