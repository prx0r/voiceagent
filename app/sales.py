"""'Call our AI' sales line: answers prospects' questions about Answered and prices.

Grounded only in knowledge/pricing.json + PITCH. Uses OpenRouter when
OPENROUTER_API_KEY is set (SALES_MODEL, default openai/gpt-4o-mini), otherwise
a keyword fallback. It never books, charges or promises anything: the close is
always "book a free call with Tom".
"""
from __future__ import annotations
import json, os, re
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
PRICING = json.loads((ROOT / "knowledge" / "pricing.json").read_text())

PITCH = """Answered: no bullshit AI for your business. Cheap AI help and tech support for UK trades and small businesses.
- Tom (a real person, the founder) does a free 20-minute setup call, then stays on hand for tech support, included.
- No subscription, no contract. Pay only for what gets used.
- Main product: an AI that answers your phone when you can't, in your own cloned voice. Emergencies are texted to you straight away; everything else lands in a 7am email. 50p a minute, only while it's actually talking. First 10 calls free. You divert missed calls to it with one code.
- Also: a website (£5 one-off), your own web address and email (£5 a year at cost), WhatsApp/Instagram/Facebook replies (20p a conversation), after-hours email agent (10p an email), after-call texts and review requests (10p a call), diary sync (free), bookings from ChatGPT (free), free optional dashboard.
- Custom AI for how you work: Tom quotes it.
- It never books or charges without the owner's rules; it only offers real free slots and takes messages.
- Per-use prices other than 50p/min, the website and the domain are draft and may change."""

SYSTEM = f"""You are the AI on Answered's own sales line. A small business owner (often a tradesperson) has rung to find out what Answered is and what it costs. You are speaking out loud on a phone call.
Rules: plain, friendly British English, no jargon, no hype. Two short sentences at most, under 40 words. Only use the facts below; if you don't know, say Tom can answer that on the free call. Never invent prices, discounts or features. Say you're an AI if asked. Where it fits, end with one short question or offer the free call with Tom. No lists, no emoji, no markdown.

FACTS:
{PITCH}

PRICING JSON:
{json.dumps({k: PRICING[k] for k in ('pack', 'usage', 'addons')}, ensure_ascii=False)}"""

GREETING = ("Hi, you're through to Answered. I'm the AI, so ask me anything: what we do, "
            "what it costs, or how setup works. What sort of business are you?")

RULES = [
    (r"\b(human|real person|tom|speak to someone|founder)\b", "Tom's the founder and a real person. He does a free 20-minute call to set everything up with you. Want me to tell you how to book it?"),
    (r"\b(cost|price|how much|charge|expensive|cheap|fee)", "Setup is free and there's no monthly fee. Answering calls is 50p a minute, only while it's talking, and your first 10 calls are free. Forty missed calls a month is about £40."),
    (r"\b(subscription|contract|monthly|cancel|tie)", "No subscription and no contract. You only pay for what gets used, and you can stop any time by turning the divert off."),
    (r"\b(website|site|web)\b", "A simple website is £5 one-off, and your own web address and email is £5 a year, at cost. The same AI answers questions in its chat."),
    (r"\b(whatsapp|instagram|facebook|meta|social|messages?)\b", "It can answer WhatsApp, Instagram and Facebook messages for 20p a conversation, and we do the Meta setup for you."),
    (r"\b(email|inbox)\b", "The after-hours email agent answers quote and booking emails for 10p each, and drafts anything tricky for you to approve."),
    (r"\b(set ?up|start|get going|install|divert|how does it work|how it works)", "Tom does a free 20-minute call: he clones your voice, loads your prices and emergency rules, and sets your phone to send missed calls to it. Then you test it together."),
    (r"\b(voice|sound like)", "It answers in your own voice. Tom clones it on the setup call from a short recording."),
    (r"\b(emergenc|urgent|out of hours|night)", "Real emergencies get texted to you straight away. Everything else is in a tidy 7am email with the caller's details."),
    (r"\b(support|broke|help|tech)", "Tech support from Tom is included. If something stops working, you message him and he sorts it."),
    (r"\b(custom|bespoke|automat|other ideas)", "If you want AI for something specific to how you work, Tom will quote it on the call. No bullshit, just what saves you time."),
    (r"\b(diary|calendar|book(ing)?s?)\b", "Diary sync is free. It offers customers your real free times and only sees busy or free, never your details."),
    (r"\b(ai|robot|bot|are you)\b", "Yes, I'm an AI, the same kind your customers would talk to. Ask me anything about prices or setup."),
    (r"\b(electric|plumb|heat|lock|barber|salon|beauty|dog|it support|builder|trade|sparky|roof|garage)", "That's exactly who it's for. It picks up the calls you miss on a job, texts you the urgent ones and books the rest. Want the prices?"),
    (r"\b(yes|yeah|sure|ok|go on)\b", "Great. Hit 'Book a free call with Tom' on the page and pick a time. It takes twenty minutes and costs nothing."),
    (r"\b(bye|thanks|thank you|cheers)\b", "Cheers for calling. Book a free call with Tom whenever suits, there's no catch."),
]

def fallback(msg: str) -> str:
    m = msg.lower()
    for pat, ans in RULES:
        if re.search(pat, m):
            return ans
    return "Good question. Simply put: free setup with Tom, no subscription, and 50p a minute when it answers your calls. Want to hear about websites or WhatsApp too?"

async def answer(msg: str, history: list[dict]) -> dict:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        msgs = [{"role": "system", "content": SYSTEM}] + [
            {"role": "user" if h.get("r") == "u" else "assistant", "content": str(h.get("t", ""))[:500]}
            for h in history[-10:]] + [{"role": "user", "content": msg[:500]}]
        try:
            async with httpx.AsyncClient(timeout=12) as c:
                r = await c.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers={"Authorization": f"Bearer {key}"},
                                 json={"model": os.getenv("SALES_MODEL", "openai/gpt-4o-mini"),
                                       "messages": msgs, "max_tokens": 120, "temperature": 0.4})
                t = r.json()["choices"][0]["message"]["content"].strip()
                if t:
                    return {"answer": t, "source": "llm"}
        except Exception:
            pass
    return {"answer": fallback(msg), "source": "rules"}
