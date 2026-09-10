# Messaging infra + vertical brains (web research, 2026-09-10 — not cloned, candidates)

## mmeganos/open-bsp-api — probable WA backbone
Self-hostable multi-tenant WhatsApp Business Platform (Deno + Supabase): official Cloud
API send/receive → Postgres; DB triggers route to agent over chat-completions or A2A;
built-in MCP client/SQL/HTTP/calculator tools; MCP server over SSE; Claude Code plugin
(query contacts/convos/templates, reply from terminal). Powers Mirlo.com agents in prod.
Use instead of hand-rolling webhook→store→dispatch: adopt if we outgrow tools/whatsapp.py.

## evolution-foundation/evolution-api — alt gateway
Big-community REST gateway: Baileys (QR, zero Meta approval — good for pilots) AND Cloud
API, plus Typebot/Chatwoot/Dify/OpenAI/RabbitMQ/Kafka/SQS/S3 integrations. Baileys =
fastest sparky pilot (scan QR, no BSP wait); migrate to Cloud API at scale. Note ToS risk
on unofficial QR path — pilot-only.

## Alessandro114/sara (AGPL-3.0 — patterns only)
WhatsApp AI with 20 vertical brains (function calling, RAG pgvector, PII anonymizer,
prompt-injection guard, autonomy OFF/OBSERVE/SEMI_AUTO/FULL_AUTO, voice notes via
Whisper, multilingual). Validates our tradie-profile.yaml direction: vertical brain >
generic bot. Steal: autonomy levels (our OBSERVE-first morning queue = SEMI_AUTO done
right), PII anonymizer before logging transcripts.

## livekit/agents (Apache 2.0 ✅) + examples
The foundation under all of the above voice work (13k★). Copy outbound-caller-python
(voicemail detect, availability lookup, human transfer) and restaurant ordering examples;
we already mirror its session model in app/session.py.

## Rule
MIT/Apache → can vendor. AGPL → read, reimplement cleanly, never paste.
