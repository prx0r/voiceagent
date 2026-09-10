# AGENTS.md — voiceagent (voice specialist box)

Read first: NORTHSTAR.md (vision), DEV_PLAN.md (build order), docs/THREADS.md (open threads).

## What this repo is
The voice lane of an agentically run trade business. Backend/social/money are canonical
in the cmail box — see cmailreaction.md for the wiring. This repo owns: real-time voice
interaction + the feedback voice owes the stack. Never canonical state, never send-out.

## Laws of this repo (violations fail review)
1. Graph is authority; LLM only words things. No business fact without evidence IDs.
2. Every side effect needs an approval/confirm token (single-use, expiring). Refuse
   destructive/security/credential classes into tickets. Nothing auto-sends or auto-orders.
3. Every contact becomes an event-fold case (app/cases.py). Conversation is not state.
4. Voice never blocks on brain reachability: local kernel answers, syncs on return.
5. Spoken quotes are ranges + validity + survey-required. Never final prices, grants,
   dates, or compliance declarations. Brain preview wording is verbatim-or-"provisional".
6. PII minimised before logging; retention enforced (app/retention.py, dry-run default).
7. AGPL repos are patterns-only — never paste (see docs/repos/). MIT/Apache may vendor.
8. Mocks prove wiring, never quality: simulated ms always labeled; no live-audio claims
   without a DID + keys run.

## Where things live
- app/: kernel (graph, llm providers, guard, tools registry, cases, session)
- app/evtools.py, tradie.py, parts.py, afterhours.py, retention.py: trade vertical
- adapters/: ears/mouth (qwen_omni corrected protocol, edge fallback)
- livekit_agent/: Telnyx worker (dumb by design — no prices/policies inside)
- mocks/: FakeSTT/LLM/TTS + Pipecat-semantics loop (speculate/rollback/barge-in)
- tools/: calendar, whatsapp (env-gated stub), meta (page/email stubs)
- knowledge/: business graphs + tradie_profile; industries/: law + competition reports
- scripts/: simulate_calls (8 night scenarios), e2e_kernel (15-step), eval_transcripts,
  curate_transcripts; static/: quote + sparky apps; tests mirror all of it.

## Dormant modules (flagged, NOT deleted — predecessors, remove only if suite stays green)
app/flow.py, app/language.py, app/subgraph.py, app/compiler.py — zero imports; logic
superseded by graph/evtools/afterhours. Doc overlaps mapped in docs/THREADS.md.

## Runbook
- tests: `python3 -m pytest tests/ -q` (must stay 36/36+; add regression test per fix)
- night sim: `python3 scripts/simulate_calls.py` (expect 8/8)
- kernel e2e: `python3 scripts/e2e_kernel.py` (expect 15/15)
- corpus drift: `python3 scripts/eval_transcripts.py` after kernel changes
- retention: `python3 -m app.retention` (dry-run; --apply deletes)
- branches: feature work on sparky-vertical; push only with fresh token, revoke after.
