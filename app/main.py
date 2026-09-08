from __future__ import annotations
import os, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
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
