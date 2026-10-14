from __future__ import annotations
import json, re
import httpx

JSON_RE = re.compile(r"\{.*\}", re.S)

class LLM:
    def __init__(self, settings):
        self.s = settings
        # Stable per-process session id: Go uses it for routing + prompt cache.
        import uuid as _uuid
        self._sid = getattr(settings, "llm_session", "") or f"ses_{_uuid.uuid4().hex}"

    @property
    def protocol(self):
        return (getattr(self.s, "llm_protocol", "") or "openai").strip().lower()

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
        headers = {"Authorization": f"Bearer {self.s.llm_api_key}", "Content-Type":"application/json",
                   "x-opencode-session": self._sid}
        if self.protocol == "responses":
            return await self._respond_responses(headers, instruction, history, message)
        url = self.s.llm_base_url.rstrip("/") + "/chat/completions"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json={"model":self.s.llm_model,"messages":msgs,"temperature":0.2})
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
        m = JSON_RE.search(text)
        if not m:
            return {"answer": text.strip(), "tool": None, "tool_args": {}, "confidence": 0.5}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {"answer": text.strip(), "tool": None, "tool_args": {}, "confidence": 0.5}

    async def _respond_responses(self, headers, instruction, history, message):
        """OpenAI Responses API (Go/Muse Spark path). Same JSON contract out."""
        turns = []
        for h in (history or [])[-8:]:
            if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content"):
                turns.append({"role": h["role"], "content": str(h["content"])[:2000]})
        turns.append({"role": "user", "content": message})
        body = {"model": self.s.llm_model,
                "instructions": instruction,
                "input": turns}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(self.s.llm_base_url.rstrip("/"), headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        text = ""
        for item in data.get("output", []) or []:
            for part in (item.get("content") or []):
                if part.get("type") in ("output_text", "text") and part.get("text"):
                    text += part["text"]
        text = text.strip()
        if not text:
            return {"answer": "The model returned no text; a human will ring you back within the hour.",
                    "tool": None, "tool_args": {}, "confidence": 0.3}
        m = JSON_RE.search(text)
        if not m:
            return {"answer": text, "tool": None, "tool_args": {}, "confidence": 0.5}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {"answer": text, "tool": None, "tool_args": {}, "confidence": 0.5}

    def _fallback(self, message: str, context: str):
        if context:
            first = context.split("\n\n")[0]
            body = " ".join(first.splitlines()[1:]).strip()
            return body[:600] or "I found relevant business information, but the LLM adapter is not configured."
        return "I can't verify that from the current business graph. Configure an LLM endpoint or add the missing policy/product/service node."
