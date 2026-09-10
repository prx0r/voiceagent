from __future__ import annotations
import json, re
import httpx

JSON_RE = re.compile(r"\{.*\}", re.S)


def parse_json_answer(text: str) -> dict | None:
    """Extract one JSON object, respecting nesting (raw_decode), with the old
    greedy fallback. Returns None when no parseable object exists."""
    if not text:
        return None
    dec = json.JSONDecoder()
    idx = text.find("{")
    while idx != -1:
        try:
            obj, _ = dec.raw_decode(text[idx:])
            if isinstance(obj, dict):
                obj.setdefault("tool", None)
                obj.setdefault("tool_args", {})
                obj.setdefault("confidence", 0.5)
                return obj
        except Exception:
            pass
        idx = text.find("{", idx + 1)
    m = JSON_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None

# Provider presets: LLM_PROVIDER picks defaults; explicit LLM_BASE_URL always wins.
# - meta: Meta Model API (Muse Spark), OpenAI-compatible Chat Completions.
# - openai: OpenAI platform. - custom/auto: whatever LLM_BASE_URL says.
PRESETS = {
    "meta": "https://api.meta.ai/v1",
    "openai": "https://api.openai.com/v1",
}


def resolve_endpoint(settings) -> str:
    """Pure: base URL -> full chat-completions URL. Unit-testable, no network."""
    base = (settings.llm_base_url or "").strip()
    if not base:
        preset = PRESETS.get((settings.llm_provider or "auto").lower(), "")
        base = preset
    return base.rstrip("/") + "/chat/completions" if base else ""

class LLM:
    def __init__(self, settings):
        self.s = settings

    @property
    def enabled(self):
        return bool(resolve_endpoint(self.s) and self.s.llm_api_key and self.s.llm_model)

    async def respond(self, system: str, history: list[dict], message: str, context: str, tools: dict):
        if not self.enabled:
            return {"answer": self._fallback(message, context), "tool": None, "tool_args": {}, "confidence": 0.45}
        instruction = f"""{system}

AUTHORITATIVE BUSINESS CONTEXT:
{context or '[no matching graph evidence]'}

AVAILABLE ACTION TOOLS:
{json.dumps(tools, ensure_ascii=False)}

Return ONLY JSON with keys:
answer: concise customer-facing answer
citations: list of graph node ids actually used
tool: null or one available tool name
tool_args: object
confidence: 0..1
needs_human: boolean

Rules:
- Never invent policy, compatibility, availability, price, order state or business facts.
- If evidence is absent, say you cannot verify it and offer the correct tool/human path.
- Never claim a tool action succeeded before the application returns success.
- Match the customer's language unless business policy requires otherwise.
"""
        msgs = [{"role":"system","content":instruction}] + history[-8:] + [{"role":"user","content":message}]
        url = resolve_endpoint(self.s)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers={"Authorization": f"Bearer {self.s.llm_api_key}", "Content-Type":"application/json"}, json={"model":self.s.llm_model,"messages":msgs,"temperature":0.2})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
        obj = parse_json_answer(text)
        if obj is None:
            return {"answer": text.strip(), "tool": None, "tool_args": {}, "confidence": 0.5}
        return obj

    def _fallback(self, message: str, context: str):
        if context:
            first = context.split("\n\n")[0]
            body = " ".join(l for l in first.splitlines()[1:]
                            if not l.startswith("META=")).strip()
            return body[:600] or "I found relevant business information, but the LLM adapter is not configured."
        return "I can't verify that from the current business graph. Configure an LLM endpoint or add the missing policy/product/service node."
