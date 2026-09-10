# VoltLine Voice-Agent — Synthesised Architecture
Sources: our kernel + AIReceptionist (patterns, AGPL — clean-room only) +
whatsapp-shopify-agent (MIT) + open-bsp/evolution (WA backbone) + sara (vertical brains)
+ LiveKit Agents + Qwen realtime + Muse Spark/Model API + competitor matrix.
 competitions: docs/competitors/. repos: docs/repos/.

## 0. One-sentence design
The kernel decides from verified state; channels (voice, WhatsApp, IG, web) only
render and capture; every side effect needs an approval token; every contact becomes
a case that outlives the call.

```
              ┌─────────────── CHANNELS (dumb, swappable) ───────────────┐
              │  PSTN→SIP→LiveKit │ Qwen realtime ears/mouth │ WA Cloud API │
              │  IG DMs (reply)   │ web /quote /sparky       │ Muse (later) │
              └──────────┬───────────────────────┬─────────────────────────┘
                         │ transcripts/events    │ render ANSWER only
              ┌──────────▼───────────────────────▼─────────────────────────┐
              │ KERNEL (the brain — ours, stays)                            │
              │ graph (facts) → LLM (words) → guard (veto) → tools (acts)   │
              │ cases (state) · tradie profile (who we serve) · audit logs  │
              └──────────┬───────────────────────┬─────────────────────────┘
                         │ reads                 │ writes (all gated)
              ┌──────────▼───────────┐ ┌─────────▼──────────────────────────┐
              │ LIVE SOURCES         │ │ GATED SIDE EFFECTS                 │
              │ calendar · catalog/  │ │ book slot · send msg · order parts │
              │ parts MCP · job feed │ │ (confirm/approval token, idempotent)│
              └──────────────────────┘ └────────────────────────────────────┘
```

## 1. Voice path (the focus)
`PSTN ─SIP trunk (Twilio/Telnyx)─→ LiveKit SIP ─room─→ AgentSession ─→ ears ─→ kernel ─→ mouth ─→ caller`
- Framework: LiveKit Agents SDK (Apache 2.0) — AgentServer, AgentSession,
  function_tool, dispatch rules, BVC telephony noise cancel. (From AIReceptionist's
  agent.py seam: realtime-model kwargs isolated so the brain is swappable.)
- Ears/mouth default: Qwen `qwen-audio-3.0-realtime-plus` WS (guaranteed WS tools;
  PCM 16k in/24k out, semantic VAD, `session.update` first — docs/QWEN_OMNI.md).
 8448kHz telephony resampled at the edge (8k→16k in, 24k→8k out) per the 3CX+Qwen build.
- Brain for wording: any OpenAI-compatible LLM — Muse Spark via Model API
  (`api.meta.ai/v1`) today, Qwen/Others tomorrow. Model never books/orders; it only
  drafts ANSWER text from graph evidence.
- Intake lifecycle (ported pattern: AIReceptionist intakes/): open → capture
  (DTMF for gate codes/fuse ratings) → confirm → close. Our /calls/intake is stage 1;
  stages 2–4 are next port.
- Transcript pipeline (ported pattern: transcript/capture→format→writer→metadata):
  every call lands verbatim + summary + triage label into the case; sparky reads the
  brief, never the raw log.

## 2. Kernel (unchanged authority)
`graph.context() → llm.respond() → guard.enforce() → tools.call() → second-pass summary`
- graph.py: TF-IDF + neighbour expansion over knowledge/*.yaml. Facts live here or they
  don't exist. (bitbybit's "live catalog per answer" is the same rule.)
- guard.py: persona/policy/authority tripwires on OUTGOING text, audited. (ShopyAgent
  markets its guardrail engine; ours is the same idea, already built.)
- Tools are tiered: safe (diagnose/qualify/triage/check) run free; moderate
  (book/propose/order) need confirm or approval tokens, single-use, expiring;
  critical (delete/security/creds) refuse into a ticket. All audited (it_audit.jsonl).
- cases/: event-fold state — survives phone→WA→van→office, model swaps, overnights.
  This is bitbybit's "one record" and our moat for services.

## 3. Tradie vertical brain (sara pattern, ours)
knowledge/tradie_profile.yaml + app/tradie.py: mornings-first, prices as RANGES,
max drive, enjoys/dislikes, calendar prefs, tone. worth_it() scores money/ease/enjoy/
distance/calendar-fit; draft_quote() ranges + validity; job stats (avg min/type) feed
back into scoring. Autonomy posture: OBSERVE-first (sara's ladder) — agent drafts and
queues; sparky taps; FULL_AUTO only per-action opt-in later (e.g. "auto-accept ≥80
weekday mornings").

## 4. After-hours loop (the money workflow)
app/afterhours.intake_call(): transcript → triage_urgency (wake_now/same_day/routine)
→ case + proposed morning slots (calendar-aware) + draft reply + quote + worth-it +
parts check → digest item with one-click actions. Wake path = push/SMS now; else
/sparky morning queue (book / send / approve-parts / on-my-way / log-time).
False-wake budget: <1/week/sparky or they mute us.

## 5. Messaging backbone (adopt, don't build)
- Pilot: Evolution-style QR gateway (zero Meta approval) → /calls/intake.
- Scale: open-bsp-style platform (Cloud API → Postgres → trigger → agent over
  chat-completions/A2A) or our tools/whatsapp.py grown up. WA = money channel
  (initiated msgs work); IG = reply-only discovery (all six competitors agree).
- Outbound shapes: text/template/document(PDF certs!)/audio — certs-in-chat is the
  electrician retention feature AnswerForMe proved.

## 6. Catalog & parts (MIT pattern)
Today: app/parts.py stub table + check→propose→approve (never auto-order).
Next: whatsapp-shopify-agent's MCP-catalog pattern — suppliers with MCP endpoints
become live stock/price reads; UCP agent-profile JSON hosted for OUR jobs/parts API
so other agents (incl. future Muse custom connectors) consume us. Same shape serves
both directions.

## 7. Surfaces
/quote (homeowner funnel: postcode+3 photos→qualify→book) · /sparky (morning queue +
feed) · /chat (web) · voice (PSTN) · WA/IG · Muse custom-connector later (needs only:
per-sparky API keys + OpenAPI docs — no Meta approval, per-user setup).

## 8. Trust & data (sara + Muse lessons)
PII anonymizer before transcript logging; retention sweeper (AIReceptionist pattern)
for runtime/ (GDPR story); training opt-out posture like Muse's; audit trails for
every gated action (guard.jsonl, it_audit.jsonl); no passwords/creds ever in context.

## 9. License boundaries (hard rules)
- MIT/Apache (Worker, livekit, open-bsp if MIT, evolution): may vendor with attribution.
- AGPL (AIReceptionist, sara): READ + REIMPLEMENT, never paste; keep clones in /tmp,
  ports described in docs/repos/*.md. Our kernel stays clean for any future licensing.

## 10. Build order (smallest diff, biggest payoff)
1. Calendar: port availability.find_slots + SlotProposal → tools/calendar.py. (Done-shape,
   kills double-books.)
2. Intake lifecycle: stages + transcript pipeline → /calls/intake + digest.
3. WA backbone: QR pilot → Cloud API; certs-as-PDF send.
4. Parts-via-MCP + our UCP profile JSON (become consumable).
5. Per-sparky API keys + OpenAPI docs (Muse-custom-connector ready).
6. Spend analytics: job stats → worth-it auto-tune; taxes export (not advice).
7. Job feed federation: shared area feed, per-tradie scoring (already stubbed).
