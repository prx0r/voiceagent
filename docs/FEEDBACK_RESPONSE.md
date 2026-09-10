# Response to cmail voiceagentfeedback/ (reviewed master@08f19c2; we answer from sparky-vertical)

Overall: accept ~80%. File:line-specific, blast-radius ordered, no fluff. Status below
is against current branch head, not what they reviewed. Disagreements noted honestly.

## 01-review — pipeline description: STALE (predates funnel/intake/afterhours/evtools)
Strengths 1-6: all still true, agreed. Structural issues:
- Two state systems: PARTIALLY FIXED (funnel/book + intake now create case + linked
  ticket). Formal session↔case join still open — accept, queue it.
- Dead code (flow/language): ACKNOWLEDGED, kept flagged per owner rule (no deletes
  without explicit say-so). Propose: we delete once their P0s need the files gone.
- .env.example / livekit in requirements / pinned Dockerfile: ACCEPTED, all still true.
- Graph scale: agreed, provenance fields queued before any Neo4j talk.

## 02-security — the important file
- P0.1 open API: PARTIALLY DONE (keys on /sparky/act + /calls/intake; 8-hex IDs remain;
  /chat//cases//graph open by design for now). Accept remainder: extend keys to /cases/*,
  unguessable IDs for new cases. Pushback: /chat stays public (it's the homeowner funnel).
- P0.2 prompt-and-hope: DONE IN SUBSTANCE (deterministic triage_urgency: escalation
  aliases + negation guard + word boundaries; auto-escalation + ticket; csec 14/14 green).
  Their app/urgency.py ≈ our evtools triage — propose name-alignment, not rebuild.
- P0.3 PII raw: ACCEPTED, biggest remaining hole. No redaction before writes; sweeper
  exists but redaction doesn't. Taking it: scrub phones/emails/addresses/passwords at
  store/case/audit write paths + tests.
- P0.4 confirm brute-force: ACCEPTED remainder (32-bit tokens, in-process, no rate limit).
  Architectural fork: they propose retiring local confirm for OUR approval tokens. Counter:
  keep local confirm for offline/single-box mode (van-WiFi rule), use brain approvals when
  connected — same pattern as slots. Joint thread.
- P0.5 subprocess allowlist: ACCEPTED (pkill/ping/journalctl unconstrained; REFUSE
  bypassable). Taking allowlists + unit/host constraints. Silver/red split: agreed in
  principle; red set lives brain-side eventually, silver stays in-call.
- P1 input guard/citation check: ACCEPTED, queued. JSON_RE greedy: ACCEPTED (one-line fix,
  taking). Secrets hygiene: ACCEPTED (.env.example now). Price-fabrication tripwire:
  ACCEPTED (their 03-integration row 4 asks for it too — taking next).

## 03-integration — contract accepted as written
Row-by-row: intake/slots/confirm/preview/telepathy setup all map to our queued P1
(adapters/brain.py). Notes back:
- Mismatch 1 (urgent detector): DONE since review — field flags are real.
- Mismatch 2 (fake book_slot): ACCEPTED — slots→confirm replaces stub; stub deleted then.
- Mismatch 3 (both IDs): ACCEPTED — carry case_id + job_id, dedupe key pattern copied.
- Mismatch 4 (calendar/shopify stubs): HALF-STALE — calendar is now real JSON (fallback
  tier); shopify still stubbed; agree shopify stays brain-side or gets deleted.
- Reverse-direction cases: agreed gate (needs our /cases auth first — extends P0.1).

## 04-build-list — mapped to our tracks
P0 items → P0.1 partial, P0.2 done, P0.3 taking now, P0.4 partial + joint fork, P0.5
taking + operational items taking. P1 → accepted as adapters/brain.py track (our UCP
profile + CONNECT docs were the unilateral version; converging to their client).
P2 → DIVERGE on Qwen loop (evidence: pipeline; settle by bake-off per DEV_PLAN);
provenance ACCEPTED; golden evals DONE in our form (night sim 8/8 + corpus 40/40 +
csec 14/14 — propose these as the shared eval set).

## Working agreement: accepted
Security P0s block production callers. We work here, they pull; big design forks go to
cmail issues tagged voiceagent. This file is the first pushback.
