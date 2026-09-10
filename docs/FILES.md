# FILES — every file, one line (audit 2026-09-10; nothing moved or deleted)

## app/ — kernel + vertical (active unless noted)
- main.py — FastAPI: /chat /funnel/* /calls/intake /sparky/* /jobs/feed /cases/*
- graph.py — TF-IDF + neighbour retrieval, evidence IDs
- llm.py — OpenAI-compatible providers (meta/openai/custom presets), nested-JSON parse
- guard.py — output tripwires incl. price-fabrication; audit
- tools.py — registry: support tools + ittools + evtools
- ittools.py — tiered IT tools (diagnose free / confirm-gated / refuse), SQLite receipts
- evtools.py — qualify_lead, triage_urgency (+negation, word-boundary, network→105)
- tradie.py — profile, worth-it scoring, quote drafts, job stats
- parts.py — catalog + approval-gated orders (+MCP hook)
- afterhours.py — intake→triage→digest, missed-only routing, catch report
- cases.py — event-fold store + brief; store.py — SQLite messages/tickets (PII tiers)
- pii.py — SECRET (never persists) vs CONTACT (cases yes, audits no) redaction
- retention.py — TTL sweeper, dry-run default; session.py — LiveKit rooms/tokens
- config.py — env settings
- flow.py, language.py, subgraph.py, compiler.py — DORMANT (zero imports; predecessors)

## adapters/ — ears/mouth: qwen_omni.py (corrected WS protocol), edge_tts.py (fallback)
## livekit_agent/ — Telnyx worker (dumb by design) + prompts + setup README
## mocks/ — FakeSTT/LLM/TTS + Pipecat-semantics loop (speculate/rollback/barge-in)
## tools/ — calendar.py (JSON slots), whatsapp.py + meta.py (env-gated stubs), shopify.py (stub)

## scripts/ — simulate_calls (8 night scenarios) · e2e_kernel (15-step) · e2e_it ·
## eval_text · eval_transcripts + curate_transcripts · compile_pack · run.sh
## tests/ — 9 files mirroring the above (39 tests); static/ — index/quote/sparky apps + UCP profile
## knowledge/ — 6 business graphs + tradie_profile · graphs/ — compiled/feed JSONs
## skill/ — sparky onboarding SKILL · handoff/ — cmail AGENTS draft + kernel schema v0.1
## Root docs: NORTHSTAR, AGENTS, DEV_PLAN, cmailreaction, FEEDBACK_RESPONSE, README, HANDOVER, BUILD_NOTES
