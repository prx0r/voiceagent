# Architecture

```text
PHONE / WEB / WHATSAPP / SHOPIFY CHAT
                 │
                 ▼
          CHANNEL ADAPTER
    LiveKit / SIP / Web / managed voice
                 │
                 ▼
           SESSION KERNEL
  trusted identity + history + state
                 │
        ┌────────┴────────┐
        ▼                 ▼
  GRAPH RETRIEVAL       TOOL ROUTER
 policies/products/     bookings/orders/
 services/FAQs          tickets/payments
        │                 │
        └────────┬────────┘
                 ▼
               LLM
   language + ambiguity resolution
                 │
                 ▼
       deterministic guardrails
                 │
                 ▼
               TTS
        Edge now / Inworld later
```

## Design rules

1. **The graph is authoritative; the LLM is not.** Prices, policy, compatibility, availability and order state must originate in graph/tool evidence.
2. **Separate public and privileged tool planes.** Shopify's reference agent separates Storefront MCP from authenticated Customer MCP. Do the same for every business.
3. **Transport identity beats model extraction.** A SIP/Twilio-authenticated caller number or logged-in customer ID cannot be overwritten by the model.
4. **Side effects are idempotent.** Booking, lead creation, refunds and payments need application-generated operation IDs and dedupe.
5. **Fast agent + slow observer.** LiveKit's advanced receptionist example uses a parallel observer that inspects conversation state and injects constraints/guardrails without slowing speech.
6. **Voice is an adapter.** Keep business graph/tools independent from Vapi/Retell/LiveKit/TTS so the vendor can be changed.
7. **Graph nodes should carry provenance.** Add `source_url`, `source_type`, `verified_at`, `evidence_status`, and `valid_from/to` before using the kernel for technical compatibility.

## Upgrade path

### Day 1
Default YAML graph + SQLite + web chat + Edge TTS.

### Day 2
Add LiveKit SIP or managed Retell/Vapi. Put phone/WhatsApp/web on the same session/ticket backend.

### Day 3
Replace graph search with Neo4j + hybrid vector retrieval. Keep `/chat` contract unchanged.

### Day 4
Add real business tools: Shopify customer/order MCP, Google Calendar, CRM/FSM, payments.

### Production
Add event log, tracing/evals, tool approval policy, worker queue/durable workflows, PII retention rules and human handoff.
