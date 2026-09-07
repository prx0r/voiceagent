# GitHub corpus: customer support / voice / supplier-agent architectures

This is the upstream map to clone and dissect. `scripts/clone_reference_repos.sh` pulls shallow copies.

## S-tier — copy architecture, not branding

### livekit/agents
**Role:** production-oriented realtime voice-agent runtime.
Study: `AgentSession`, tool calls, interruption handling, turn detection, provider plugins, worker/session lifecycle.
**Use here:** preferred production channel layer.

### livekit-examples/python-agents-examples
**Role:** executable design patterns.
Highest-value example: `complex-agents/doheny-surf-desk` — phone receptionist with Intake/Scheduler/Gear/Billing/FrontDesk agents plus a slower parallel Observer agent, structured task groups and context injection.
**Use here:** canonical multi-step receptionist workflow.

### livekit/sip
**Role:** phone/SIP bridge.
**Use here:** own telephony transport rather than tying business state to a managed voice vendor.

### pipecat-ai/pipecat
**Role:** composable realtime audio frame pipeline.
Study: STT→LLM→TTS frames, interruption/barge-in, transports, processors.
**Use here:** alternative to LiveKit when low-level provider control matters.

### bolna-ai/bolna
**Role:** open-source hosted-style voice orchestration backend.
Architecture observed: Twilio/Plivo → WebSocket; Deepgram/Azure STT; multiple LLMs; ElevenLabs/Deepgram/OpenAI/Cartesia/etc TTS; Redis persistence.
**Use here:** reference for provider abstraction and multi-tenant voice backend.

### TEN-framework/ten-framework
**Role:** realtime multimodal/SIP framework with VAD and turn-detection subprojects.
**Use here:** independent architecture reference and multilingual realtime patterns.

### codewithmuh/hearthline
**Role:** closest open home-services AI front desk found.
Study: lead qualification, quote drafting, availability, booking, CRM records, Vapi/Twilio integrations, **per-call tool-result dedupe**.
**Key scar:** tool calls can repeat; cache/dedupe side effects by trusted call/session identity.

## Shopify / ecommerce support

### Shopify/shop-chat-agent
Official storefront support/shopping-agent template.
Architecture: React Router backend + Claude + Shopify MCP; separately connects Storefront MCP and customer-authenticated MCP. Supports product search, policies/FAQs, cart, checkout, order status and returns.
**Steal:** public-vs-customer tool-plane separation and auth-on-demand.

### Shopify/ucp-cli
Agent-facing Shopify Global Catalog/UCP tooling.
**Steal:** catalog query/filters and machine-commerce boundaries.

### Universal-Commerce-Protocol/ucp
Cross-industry commerce/service capability schemas.
**Steal:** Location/serviceability, request constraints, carts/checkout/fulfillment semantics.

### agentic-commerce-protocol/agentic-commerce-protocol
ACP checkout/product-feed specification.
**Steal:** product feeds, session state, merchant/agent transaction contract.

### daydreamsai/lucid-agents
Typed machine-commerce runtime: discovery, policy, idempotency, fulfillment, x402/MPP payments, identity, A2A and scheduling.
**Steal:** typed capability registry and side-effect admission.

### paypal/agent-toolkit + stripe/ai
Real financial tool surfaces for invoices/orders/refunds/disputes/subscriptions/payment actions.
**Steal:** treat finance as typed tools with narrow scopes, never prompt-only actions.

## Graph / memory / durable state

### openreferral/specification
Long-running open schema for organization → service → location → accessibility relationships.
**Steal:** mature service-directory graph vocabulary.

### neo4j/neo4j-graphrag-python
Production graph + retrieval patterns.
**Upgrade:** replace MVP lexical graph while retaining evidence IDs/provenance.

### mem0ai/mem0
Long-term memory framework.
**Use:** customer preferences/history only after defining retention/privacy boundaries. Do not mix volatile memory with authoritative policy/product truth.

### langchain-ai/langgraph
Stateful graph orchestration for long-running/multi-step agents.
**Use:** useful if business workflow becomes branching and human-in-the-loop.

### temporalio/samples-python
Durable execution/retry/idempotency reference.
**Use:** booking, refund, supplier bid and payment workflows that must survive process failure.

### openai/openai-agents-python / google/adk-python
Modern general agent runtimes.
**Use:** compare tool/handoff/eval semantics; keep core business state outside framework-specific memory.

## Dispatch / supplier OS

### TimefoldAI/timefold-quickstarts + timefold-solver
Constraint optimization.
**Steal:** hard feasibility first, assignment second, travel/cost/fairness optimization last. This is the correct architecture for technician dispatch; don't ask an LLM to pick technicians directly.

## Agent-commerce intelligence / evals

### NVIDIA-AI-Blueprints/Retail-Agentic-Commerce
Open retail recommendation/promotion reference with retrieval, NLI alignment scoring and deterministic inventory/margin guards.

### anthropics/commerce-agents
Commerce-agent reference implementation; useful ranking/tool/eval patterns.

### Accio-org/BusinessArena + CommerceAgentBench
Long-horizon ecommerce/business-agent environments. Useful for eval harness design.

### arenza-ai/agentic-commerce-score
Agent-commerce readiness scoring. Useful reference for external observability and catalog QA.

## Recommended production stack for this kernel

```text
Telephony:     LiveKit SIP (or Retell/Vapi to launch immediately)
STT:           Deepgram or frontier realtime model
LLM:           fast OpenAI-compatible model; Hermes/OpenRouter works
TTS:           Inworld / Cartesia / Deepgram / ElevenLabs
Graph truth:   Postgres + Neo4j if relationship complexity warrants it
Retrieval:     graph entity lookup + lexical/vector hybrid + provenance
Workflow:      plain typed tools first; Temporal for durable side effects
Customer UI:   web widget + phone + WhatsApp adapter
Observability: structured events + conversation/tool traces + evals
```
