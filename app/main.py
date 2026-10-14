from __future__ import annotations
import os, uuid, json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
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
    trade: str | None = None  # demo: answer as that trade's sample business

@app.get("/")
def home():
    return FileResponse("static/home.html")

@app.get("/t/{trade}")
def trade_console(trade: str):
    if not _trade_kernel(trade):
        raise HTTPException(404, "unknown trade")
    return FileResponse("static/app.html")


def _mcp_biz(trade: str):
    from . import mcp as _mcp
    kern = _trade_kernel(trade)
    if not kern:
        raise HTTPException(404, "unknown trade")
    hours = {}
    try:
        d = next(i for i in api_industries()["industries"] if i["slug"] == trade)
        hours = d.get("hours") or {}
    except StopIteration:
        pass
    from . import workflows as _wf
    return _mcp.Biz(trade, kern[2], hours, SAMPLE_PRICES.get(trade, []), "Manchester",
                    triage=lambda text: _wf.triage(trade, kern[2], text))


_MCP_HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}


@app.post("/mcp/{trade}")
async def mcp_post(trade: str, request: Request):
    from fastapi.responses import JSONResponse, Response
    from . import mcp as _mcp
    b = _mcp_biz(trade)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}, 400, headers=_MCP_HEADERS)
    if isinstance(body, list):
        out = [r for r in (_mcp.handle(b, m) for m in body) if r]
        return JSONResponse(out, headers=_MCP_HEADERS) if out else Response(status_code=202, headers=_MCP_HEADERS)
    r = _mcp.handle(b, body)
    return JSONResponse(r, headers=_MCP_HEADERS) if r else Response(status_code=202, headers=_MCP_HEADERS)


@app.options("/mcp/{trade}")
def mcp_options(trade: str):
    from fastapi.responses import Response
    return Response(status_code=204, headers=_MCP_HEADERS)


@app.get("/mcp/{trade}")
def mcp_get(trade: str, request: Request):
    from fastapi.responses import Response
    from . import mcp as _mcp
    b = _mcp_biz(trade)
    if "text/event-stream" in request.headers.get("accept", ""):
        return Response(status_code=405, headers={**_MCP_HEADERS, "Allow": "POST"})  # stateless: no server-initiated stream
    return {"name": f"{b.name} receptionist", "transport": "streamable-http", "endpoint": f"/mcp/{trade}",
            "protocol": _mcp.PROTOCOL, "tools": [t["name"] for t in _mcp.TOOLS],
            "connect": "Add as a custom connector (MCP) in ChatGPT or Claude using this URL."}

@app.get("/landing")
def landing():
    return FileResponse("static/landing.html")

@app.get("/kernel")
def kernel():
    return FileResponse("static/index.html")

@app.get("/grid")
def grid():
    return FileResponse("static/grid.html")

_TRADE_CACHE: dict = {}


def _trade_kernel(slug: str):
    """(business config, graph, sample name) for a demo trade, cached."""
    if slug in _TRADE_CACHE:
        return _TRADE_CACHE[slug]
    from . import industries as site_data
    meta = next((t for t in site_data.TRADES if t["slug"] == slug), None)
    if not meta:
        return None
    try:
        cfg = site_data.load_pack(meta["file"])
    except OSError:
        return None
    name = SAMPLE_BIZ.get(slug, "Sample & Sons")
    _TRADE_CACHE[slug] = (cfg, KnowledgeGraph(cfg), name)
    return _TRADE_CACHE[slug]


def _re_urgent(msg: str) -> bool:
    import re as _re
    return bool(_re.search(r"(?i)\b(locked out|lockout|urgent|emergency|no heating|no hot water|"
                           r"burst|leak|flood|gas|spark\w*|burning|smoke|offline|down|hacked|injur\w*|bleed\w*|tonight|no power|"
                           r"phishing|ransom\w*|priority 1|water everywhere|ceiling|break-?in)\b", msg))


def _re_symptom(msg: str) -> bool:
    import re as _re
    return bool(_re.search(r"(?i)\b(trip(s|ping)?|keeps|won'?t|not working|stopped|broken|faulty|leak(s|ing)?|"
                           r"no (power|heating|hot water)|dripping|blocked|offline|can'?t|pressure|fault code|error code|flicker\w*)\b", msg or ""))


def _receptionist_fallback(message: str, evidence: list, biz: str, g, slug: str = "", urgent: bool | None = None) -> str:
    _urg = (lambda m: urgent) if urgent is not None else _re_urgent
    """No-LLM demo reply: receptionist tone, built only from graph evidence."""
    ids = [e.get("id", "") for e in (evidence or [])]
    nodes = [g.nodes.get(i, {}) for i in ids]
    esc_n = next((n for n in nodes if n.get("type") == "escalation"), None)
    urgent_svc = next((n for n in nodes if n.get("type") == "service"
                       and "emergency" in (n.get("id", "") + n.get("name", "")).lower()), None)
    if not esc_n and urgent_svc and _urg(message):
        esc_n = urgent_svc
    import re as _r0
    if esc_n and not _urg(message):
        esc_n = None  # an escalation node in the evidence isn't enough; the caller has to sound urgent
    if not esc_n and _urg(message) and not _r0.search(r"(?i)\b(how much|price|cost|quote)\b", message):
        esc_n = {"text": ""}
    if esc_n and not _urg(message) and _r0.search(r"(?i)\b(how much|price|cost|quote|fit|install|book)\b", message):
        esc_n = None  # a pricing/booking question that merely mentions a plumbing word is not an emergency
    svc = next((n for n in nodes if n.get("type") == "service"), None)
    # A symptom ("keeps tripping", "won't work", "leaking") is a repair job, not an upgrade sale.
    if _re_symptom(message):
        fix = next((n for n in nodes if n.get("type") == "service" and any(
            k in (n.get("id", "") + " " + n.get("name", "")).lower()
            for k in ("fault", "repair", "breakdown", "leak", "fix", "unblock", "diagnos", "support"))), None)
        svc = fix or svc
    pol = next((n for n in nodes if n.get("type") in ("policy", "faq")), None)
    from .industries import _clean
    import re as _re

    def needs(n):
        """'X. Needs: a, b. Typical...' -> ('X.', 'a, b')"""
        t = _clean(n.get("text", ""), biz)
        m = _re.search(r"Needs?:\s*([^.]+)\.?", t)
        rest = _re.sub(r"\s*Needs?:\s*[^.]+\.?", "", t).strip()
        return rest, (m.group(1).strip() if m else "")
    if esc_n:
        t = _clean(esc_n.get("text", ""), biz)
        safety = " ".join(x.strip() for x in _re.split(r"(?<=\.)\s+", t)
                          if _re.match(r"(?i)\s*tell (the )?(customer|caller)", x))
        safety = _re.sub(r"(?i)^tell (the )?(customer|caller) (to )?", "", safety).strip()
        safety = _re.sub(r"\band not to\b", "and don't", safety).replace("/", " or ")
        tip = f" Meanwhile, please {safety[0].lower() + safety[1:]}" if safety else ""
        if tip and not tip.endswith("."):
            tip += "."
        if not tip and slug and slug != "soletrader":
            from .mcp import SAFETY
            if slug in SAFETY:
                tip = " " + SAFETY[slug]
        if _re.search(r"(?i)\bgas\b", message):
            tip = (" Please leave the property, don't touch any switches, and ring the National Gas Emergency line"
                   " on 0800 111 999 now.")
        return (f"That sounds urgent, so I'm alerting whoever's on call right now.{tip} "
                "What's your name, the address, and the best number to ring you on?")
    if svc:
        rest, need = needs(svc)
        first = rest.split(". ")[0].rstrip(".") if rest else ""
        def lc(x):  # keep acronyms: "EV charger" stays, "Leak repair" -> "leak repair"
            return " ".join(w if w[:2].isupper() else w.lower() for w in x.split())
        line = f"Yes, we can help with {lc(svc.get('name', 'that'))}."
        when = _re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", message)
        booking = _re.search(r"(?i)\b(book|appointment|slot)\b", message)
        price_q = _re.search(r"(?i)\b(how much|price|cost|quote|charge)\b", message) or booking
        pa = _price_answer(slug, message + " " + svc.get("name", "")) if price_q else ""
        if pa:
            line += " " + pa
        elif price_q and pol is not None and "pric" in (pol.get("id", "") + pol.get("name", "")).lower():
            line += " " + _clean(pol.get("text", ""), biz).split(". ")[0].rstrip(".") + "."
        if need:
            parts = [x.strip().lower() for x in _re.split(r",|\band\b", need) if x.strip()]
            joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
            lead = "To get you booked in" if pa else "So the team can come prepared"
            line += f" {lead}, it helps to know: {joined}."
        if (first and len(first) < 90 and len(first.split()) >= 4 and '—' not in first
                and not first.lower().startswith(("home", svc.get("name", "").lower()[:6]))):
            line += f" {first}."
        if booking and when:
            line += f" I'll hold {when.group(0)} for you and the confirmation comes by text."
        tail = (" And your name and best number, and you'll hear back first thing with times." if need
                else " Can I take your name and best number? You'll hear back first thing with times.")
        return line + tail
    if _re.search(r"(?i)\b(how much|price|cost|charge)\b", message) and _price_answer(slug, message):
        return _price_answer(slug, message) + " Want me to get you booked in? I just need your name and number."
    if pol:
        return (f"{_clean(pol.get('text', ''), biz)} "
                "Want me to pass your details on so they can confirm properly?")
    return (f"Thanks for calling {biz}. Nobody can pick up right now, but I'll make sure this reaches them first thing. "
            "What's your name, your number, and a line about the job?")


SAMPLE_BIZ = {
    "electrician": "Dave's Electrical", "plumber": "Flowright Plumbing",
    "heating": "CosyHeat", "locksmith": "Keyline Locks",
    "beauty": "Glow Studio", "barber": "Fade Factory",
    "dogwalker": "Happy Tails", "msp": "Nimbus IT",
}

# Published guide prices for the SAMPLE businesses on the demo sites (illustrative,
# inc. VAT). A real customer's site uses their own list from onboarding.
SAMPLE_PRICES = {
    "electrician": [["Callout and first hour", "£85"], ["Fault finding", "from £95"],
                    ["Extra double socket", "from £120"], ["EV charger installed", "from £895"],
                    ["Consumer unit upgrade", "from £550"], ["EICR safety report", "from £160"]],
    "plumber": [["Callout and first hour", "£80"], ["Leak repair", "from £95"],
                ["Annual boiler service", "£89"], ["Tap or toilet repair", "from £75"],
                ["Emergency out of hours", "from £150"]],
    "heating": [["Boiler service", "£89"], ["Boiler repair visit", "from £110"],
                ["Power flush", "from £395"], ["Gas safety certificate", "£75"],
                ["Emergency callout", "from £150"]],
    "locksmith": [["Lockout, daytime", "from £79"], ["Lockout, after 6pm", "from £119"],
                  ["Lock change (euro cylinder)", "from £95"], ["Anti-snap upgrade", "from £120"]],
    "beauty": [["Gel manicure", "£32"], ["Gel pedicure", "£38"], ["Lash lift and tint", "£45"],
               ["Brow shape and tint", "£22"], ["Facial, 60 min", "£55"]],
    "barber": [["Skin fade", "£22"], ["Scissor cut", "£24"], ["Beard trim", "£12"],
               ["Fade and beard", "£30"], ["Kids cut (under 12)", "£15"]],
    "dogwalker": [["Solo walk, 60 min", "£18"], ["Group walk, 60 min", "£14"],
                  ["Puppy visit, 30 min", "£12"], ["Home boarding, per night", "£40"]],
    "msp": [["Managed IT, per user", "£45 a month"], ["Remote support, per hour", "£75"],
            ["On-site visit", "from £120"], ["Microsoft 365 migration", "from £850"]],
    "soletrader": [["Callout", "from £60"], ["Hourly rate", "from £45"], ["Free quote visit", "£0"]],
}


def _price_answer(slug: str, message: str) -> str:
    import re as _re
    words = set(_re.findall(r"[a-z]{3,}", message.lower())) - {"how", "much", "price", "cost", "the", "for", "and", "you", "your", "does"}
    best = None
    for name, price in SAMPLE_PRICES.get(slug, []):
        hit = len(words & set(_re.findall(r"[a-z]{3,}", name.lower())))
        if hit and (best is None or hit > best[0]):
            best = (hit, name, price)
    if best:
        return f"Our guide price for {' '.join(w if w[:2].isupper() else w.lower() for w in best[1].split())} is {best[2]}, and the exact figure is confirmed before any work starts."
    return ""


CUSTOMER_TAGLINE = {
    "electrician": "Qualified electricians for homes and small businesses, from new sockets to emergency faults.",
    "plumber": "Leaks, blockages, taps and bathrooms, fixed properly and priced up front.",
    "heating": "Boiler repairs, servicing and installs that keep your home warm all winter.",
    "locksmith": "Lockouts, lock changes and security upgrades, with fast local response.",
    "beauty": "Nails, lashes and brows in a calm, friendly studio. Book in seconds.",
    "barber": "Sharp fades, classic cuts and beard work. Walk in or book ahead.",
    "dogwalker": "Reliable walks, visits and sitting from people who love dogs as much as you do.",
    "msp": "Friendly IT support for small offices: fixes, security and new starters handled.",
    "soletrader": "Local, reliable and straight-talking. Tell us about the job.",
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
                 "TAGLINE": CUSTOMER_TAGLINE.get(slug, meta["tagline"]), "AREA": area,
                 "SLUG": slug}.items():
        html = html.replace("{{" + k + "}}", v)
    html = html.replace("</head>", _agent_discovery(slug, biz, area) + "</head>", 1)
    return HTMLResponse(html)


def _agent_discovery(slug: str, biz: str, area: str) -> str:
    """JSON-LD + link rels so AI assistants find the business's MCP receptionist from its website."""
    ld = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": biz, "areaServed": area,
          "url": f"/demo/{slug}",
          "makesOffer": [{"@type": "Offer", "name": n, "description": f"Guide price {p}"} for n, p in SAMPLE_PRICES.get(slug, [])],
          "potentialAction": {"@type": "ReserveAction", "name": "Request a booking via MCP",
                              "target": {"@type": "EntryPoint", "urlTemplate": f"/mcp/{slug}",
                                         "encodingType": "application/json", "contentType": "application/json"}}}
    return (f'<link rel="mcp" href="/mcp/{slug}"><link rel="alternate" type="text/plain" href="/demo/{slug}/llms.txt" title="llms.txt">'
            f'<script type="application/ld+json">{json.dumps(ld)}</script>')


@app.get("/demo/{trade}/llms.txt")
def demo_llms(trade: str):
    from fastapi.responses import PlainTextResponse
    from . import console as con
    kern = _trade_kernel(trade)
    if not kern:
        raise HTTPException(404, "unknown trade")
    biz, si = kern[2], con.site(trade)
    lines = [f"# {biz}", "", f"> {CUSTOMER_TAGLINE.get(trade, '')} Manchester. Phone answered 24/7.", "",
             "## For AI assistants",
             f"- MCP receptionist (streamable HTTP): /mcp/{trade}",
             "- Tools: get_business_info, list_services, check_availability, request_booking, report_emergency, leave_message",
             "- Bookings are requests until the business confirms by text. Guide prices only.", "",
             "## Services and guide prices"] + [f"- {n}: {p}" for n, p in SAMPLE_PRICES.get(trade, [])] + \
            ["", "## What customers usually need"] + [f"- {w}" for w in si["why"]]
    return PlainTextResponse("\n".join(lines) + "\n")

@app.get("/app")
def app_shell():
    return FileResponse("static/app.html")

@app.get("/site")
def site():
    return FileResponse("static/site.html")

@app.get("/api/industries")
def api_industries():
    from . import industries as site_data
    d = site_data.industries()
    for i in d["industries"]:
        i["business"] = SAMPLE_BIZ.get(i["slug"], "Sample & Sons")
        i["area"] = "Manchester"
        i["price_list"] = SAMPLE_PRICES.get(i["slug"], [])
        dflt = {"monday-friday": "08:00-18:00", "saturday": "09:00-13:00", "sunday": "closed"}
        i["hours"] = {k: (dflt.get(k, "closed") if "[" in str(v) else v) for k, v in (i.get("hours") or {}).items()}
    return d

class GuideIn(BaseModel):
    trade: str
    message: str
    session_id: str | None = None
    done: list[str] = []


@app.get("/api/console/calendar")
def console_calendar(trade: str):
    from . import console as con
    return con.calendar(trade)


@app.get("/api/console/{trade}")
def console_boot(trade: str):
    from . import console as con
    kern = _trade_kernel(trade)
    if not kern:
        raise HTTPException(404, "unknown trade")
    cfg, _, biz = kern
    from .industries import _clean
    pack_name = str((cfg.get("business", {}) or {}).get("name", ""))
    rp = str((cfg.get("agent", {}) or {}).get("system_prompt", ""))
    if pack_name:
        rp = rp.replace(pack_name, biz)
    return {"trade": trade, "business": biz, "opening": con.opening(trade, biz), "stats": con.stats(trade),
            "site": con.site(trade), "mcp": f"/mcp/{trade}",
            "prompts": con.funnel(trade, set()),
            "system_prompts": {"guide": con.guide_prompt(trade, biz), "receptionist": _clean(rp, biz)},
            "brief": {k: v for k, v in con.brief(trade).items() if k in ("emergency", "booking", "price_q")}}


@app.post("/api/console/guide")
async def console_guide(inp: GuideIn):
    from . import console as con
    kern = _trade_kernel(inp.trade)
    if not kern:
        raise HTTPException(404, "unknown trade")
    biz = kern[2]
    out = con.guide_answer(inp.trade, biz, inp.message[:500], set(inp.done or []))
    if llm.enabled:
        sid = inp.session_id or str(uuid.uuid4())
        hist = store.history("guide:" + sid, 8)
        r = await llm.respond(con.guide_prompt(inp.trade, biz), hist, inp.message[:500],
                              con.PRODUCT + "\n" + con.calendar_context(inp.trade), {})
        if r.get("answer"):
            out["answer"] = r["answer"]
        store.add_message("guide:" + sid, "user", inp.message[:500], {})
        store.add_message("guide:" + sid, "assistant", out["answer"], {})
        out["session_id"] = sid
    return out


@app.get("/health")
def health():
    return {"ok": True, "business": business.get("business",{}).get("name"), "llm": llm.enabled, "nodes": len(graph.nodes)}

@app.post("/chat")
async def chat(inp: ChatIn):
    sid = inp.session_id or str(uuid.uuid4())
    store.add_message(sid, "user", inp.message, {"locale": inp.locale})
    kern = _trade_kernel(inp.trade) if inp.trade else None
    g = kern[1] if kern else graph
    context, evidence = g.context(inp.message)
    hist = store.history(sid, 10)
    if kern:
        cfg, _, biz_name = kern
        pack_name = str((cfg.get("business", {}) or {}).get("name", ""))
        sys = str((cfg.get("agent", {}) or {}).get("system_prompt", "You are a warm after-hours receptionist."))
        if pack_name:
            sys = sys.replace(pack_name, biz_name)
        from .industries import _clean
        sys = _clean(sys, biz_name) + " Keep replies to two or three short spoken sentences."
    else:
        sys = business.get("agent",{}).get("system_prompt", "You are a precise customer support agent.")
    from . import console as _con
    from . import workflows as _wf
    tri = _wf.triage(inp.trade, kern[2], inp.message) if kern else None
    if tri and tri.get("status") == "complete":
        context = (context + f"\n\nTRIAGE (Jev, typed): {json.dumps(tri.get('output'))}").strip()
    elif tri:
        tri = {**tri, "output": {"action": "take_message", "priority": "p3", "intent": "unclear"}}
    wants_slot = bool(kern) and bool(__import__("re").search(
        r"(?i)\b(when|come|available|availability|slots?|today|tonight|tomorrow|afternoon|morning|this week|next week|book|appointment|visit|free)\b", inp.message)) \
        and not (_re_urgent(inp.message) if not tri else tri["output"]["action"] == "alert_owner_now") and not __import__("re").search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", inp.message)
    if tri:
        wants_slot = tri["output"].get("action") in ("offer_slots", "check_diary", "reschedule") \
            and not __import__("re").search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", inp.message)
    if kern:
        context = (context + "\n\n" + _con.calendar_context(inp.trade)).strip()
    if kern and not llm.enabled:
        tri_urgent = None if not tri else (tri["output"] or {}).get("action") == "alert_owner_now"
        if tri_urgent is False and evidence:
            # Non-urgent call: don't let an emergency service node answer a routine ask.
            calm = [e for e in evidence if "emergenc" not in str(e).lower()]
            if calm:
                evidence = calm
        ans = _receptionist_fallback(inp.message, evidence, kern[2], g, inp.trade, urgent=tri_urgent)
        if wants_slot:
            import re as _r2
            ans = _r2.sub(r"(?i)[,\s]*(and )?you'll hear back first thing with times\.?", ".", ans).strip()
            ans = _r2.sub(r"\.\.+", ".", ans).replace("?.", "?")
            ans = _r2.sub(r"\s*Want me to get you booked in\? I just need your name and number\.?", "", ans).strip()
            ans = (ans + " " + _con.slots_sentence(inp.trade, inp.message)).strip()
        if tri and tri.get("status") == "complete":
            act, it = tri["output"].get("action"), tri["output"].get("intent")
            if act == "alert_owner_now" and tri["output"].get("vulnerable"):
                ans = ans.replace("right now.", "right now, and I've flagged that someone vulnerable is affected.", 1)
            elif act == "reschedule":
                ans = ("No problem, I can move that for you. What name is the booking under? "
                       + _con.slots_sentence(inp.trade, inp.message)).strip()
            elif act == "give_price" and "£" not in ans:
                ans = (f"Prices depend on the job, so {kern[2]} confirms an exact figure before any work starts. "
                       "What's the job, and your name and best number?")
            if act == "drop_spam":
                ans = f"Thanks, but {kern[2]} doesn't take sales calls on this line. Goodbye."
            elif act == "take_message" and (it == "complaint" or (tri.get("call") or {}).get("wants_human")):
                ans = (("I'm sorry to hear that. " if it == "complaint" else "") +
                       "I'll pass this straight to the owner, who'll ring you back personally. What's your name and best number?")
        result = {"answer": ans, "tool": None, "tool_args": {}, "confidence": 0.5}
    else:
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
    return {"session_id": sid, "answer": result.get("answer"), "evidence": evidence, "triage": tri if kern else None, "tool": result.get("tool"), "tool_result": tool_result, "confidence": result.get("confidence"), "audio_url": audio_url}

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
