# Supplier Support Agent Kernel

Reusable graph-grounded customer-support / receptionist MVP designed to be adapted to almost any service business or technical ecommerce store.

## 60-second start

```bash
cp .env.example .env
pip install -r requirements.txt
./scripts/run.sh
# open http://localhost:8080
```

It runs without an LLM key in retrieval-only fallback mode. For real conversation, set any OpenAI-compatible `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`.

## Adapt to a business

Copy `knowledge/generic_service_business.yaml`, then change:

- business identity/hours
- policies
- services/products
- FAQs
- escalation rules
- graph edges
- `BUSINESS_CONFIG` in `.env`

No application-code edits are required for basic adaptation.

## Voice

Edge TTS is included as a disposable demo TTS. Production recommendation is to keep the same business kernel and swap the channel layer for LiveKit + SIP and the TTS adapter for Inworld/Cartesia/Deepgram/etc.

## API

- `POST /chat` — graph-grounded conversation
- `GET /graph/search?q=...` — inspect what the agent retrieves
- `GET /health`

Example:

```bash
curl -s localhost:8080/chat -H 'content-type: application/json' \
  -d '{"message":"Can I return a part?","speak":false}' | jq
```

## Why a graph?

Customer support questions are mostly relationships, not documents:

```text
PRODUCT → compatible_with → ASSET
SERVICE → governed_by → POLICY
LOCATION → offers → SERVICE
PART → supersedes → PART
CUSTOMER → owns → ASSET
ORDER → contains → PRODUCT
```

The LLM handles language and ambiguity; authoritative facts stay in graph/tool evidence.

## Upstream research corpus

Run:

```bash
./scripts/clone_reference_repos.sh
```

See `docs/REPO_COMPILATION.md` for what to inspect and why.

## Important MVP limitations

- YAML graph search is lexical + neighbour expansion, not production GraphRAG.
- Booking/order tools are stubs.
- No PSTN transport is wired by default.
- Edge TTS requires network access and is not the intended production voice.
- Add provenance, permissions, PII controls, durable workflows and evals before real autonomous refunds/payments/bookings.
