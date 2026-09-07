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

settings = Settings()
business = Settings.load_business(settings.business_config)
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
    if result.get("tool"):
        tool_result = tools.call(result["tool"], result.get("tool_args") or {}, sid)
        # Never pretend success. Give the model one deterministic summary for MVP.
        if tool_result.get("ok"):
            result["answer"] = result.get("answer", "") + f"\n\nAction result: {tool_result}"
        else:
            result["answer"] = result.get("answer", "") + "\n\nI couldn't complete that action; a human should take over."
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
