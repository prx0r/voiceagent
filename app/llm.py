from __future__ import annotations
import json, re
import httpx

JSON_RE = re.compile(r"\{.*\}", re.S)

class LLM:
    def __init__(self, settings):
        self.s = settings

    @property
    def enabled(self):
        return bool(self.s.llm_base_url and self.s.llm_api_key and self.s.llm_model)

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
        url = self.s.llm_base_url.rstrip("/") + "/chat/completions"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers={"Authorization": f"Bearer {self.s.llm_api_key}", "Content-Type":"application/json"}, json={"model":self.s.llm_model,"messages":msgs,"temperature":0.2})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
        m = JSON_RE.search(text)
        if not m:
            return {"answer": text.strip(), "tool": None, "tool_args": {}, "confidence": 0.5}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {"answer": text.strip(), "tool": None, "tool_args": {}, "confidence": 0.5}

    def _fallback(self, message: str, context: str):
        if context:
            first = context.split("\n\n")[0]
            body = " ".join(first.splitlines()[1:]).strip()
            return body[:600] or "I found relevant business information, but the LLM adapter is not configured."
        return "I can't verify that from the current business graph. Configure an LLM endpoint or add the missing policy/product/service node."
