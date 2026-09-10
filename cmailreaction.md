# Reaction: cmail stack (cloned 2026-09-10, reviewed from this box)

Source: `github.com/prx0r/cmail` (/tmp/opencode/cmail) — cmail email bus (LIVE on
Workers) + stevejobless brain (69/69 pytest, intake→invoice live) + VOICE_COMPAT.md
contract. This doc is the voice side's reply: what we accept, where we diverge,
and the exact wiring to connect.

## 1. Accept: the ownership split
Voice owns conversation, brain owns business. Correct and we will conform:
transcript + urgency judgement flow voice→brain; jobs/quotes/slots/verdicts flow
brain→voice; send-out (WA/IG/email) is brain-only — our `/sparky/act send_response`
becomes a brain call when connected (local stub stays as offline fallback).
Quote-preview rule accepted verbatim: read `options[].preview` exactly when
`needs_review=false`, else say "provisional". Shared kernel YAML accepted: one file,
two consumers — we adopt their `knowledge/<biz>_en.yaml` schema (superset of our
tradie_profile.yaml) and map ours onto it.

## 2. Diverge (with evidence): Qwen-Omni realtime as the voice runtime
VOICE_COMPAT §"Muse verdict" recommends Qwen realtime S2S. Our research says pipeline:
Qwen realtime is every paper's *baseline*, WS tool docs contradict, token billing punishes
big prompts, and S2S can't show which fact grounded which sentence — fatal when quoting
money. Proposed resolution, not argument: bake-off on their own metric (intake→draft
latency + verdict accuracy). Our mocks/ loop already runs both shapes; first real DID
decides with data. Until then we build the pipeline path and keep the S2S seam open
(adapters/qwen_omni.py stays).

## 3. Overlaps to reconcile (we both built these — converge, don't fork)
| Piece | Ours | Theirs (brain) | Resolution |
|---|---|---|---|
| Tradie kernel | knowledge/tradie_profile.yaml | knowledge/<biz>_en.yaml + tradie block | Adopt theirs as canonical; ours becomes a reader + offline cache |
| Triage | evtools.triage_urgency | intake priority/wake-now | Ours runs in-call (latency); theirs is record (their HumanAction queue wins on conflict) |
| Scoring/quotes | tradie.worth_it/draft_quote | jobs/quotes/stats calibration | Ours drafts pre-brain-contact; once job exists, brain preview is canonical |
| Slots | tools/calendar.py JSON | /slots (live Google freebusy) | Their endpoint when connected; ours offline fallback |
| Telephony setup | livekit_agent scaffold | /telnyx/wire + /livekit/sip-config | They own setup; we consume sip-config, fix listed problems first |
| Cases | runtime/cases event-fold | Jobs + HumanAction queue | Map: our case = their Job's voice leg; close-out syncs both ways |

## 4. Endpoint wiring (voice → brain)
- `POST /api/tradie/{slug}/intake` replaces local intake_call when reachable
  (same payload shape as our IntakeIn + transcript + urgent flag; expect one-click
  options back: quote draft, ICS, call-back, verdict).
- `GET /api/tradie/{slug}/slots` → spoken availability; `POST .../jobs/{id}/confirm`
  to lock. Our free_slots stays as fallback when brain unreachable (van Wi-Fi rule).
- `GET /api/tradie/{slug}/jobs/{id}` options[].preview → speak verbatim policy above.
- Health rule: voice never blocks a call on brain reachability — local kernel answers,
  syncs when back. Every brain call gets timeout + fallback + audit note.

## 5. Their gaps that are our lane (confirmed)
Voice runtime + DID + TTS bake-off + availability hardening = this repo's queue, in
that order. Credentials/pilot-sparky block both sides equally — single joint onboarding
session covers brain + voice (merge SKILL.md checklists; one 15-min call, not two).

## 6. Risks we share (both noted independently — good sign)
Meta squeeze (both mitigations identical: official APIs, multi-channel, business-process
framing), secret sprawl (vault; rotate the systemd/tunnel tokens), single SQLite
(brain needs the R2 nightly copy before revenue), AGPL patterns-only (both sides clean).

## 7. Suggested joint next steps
1. Lock the shared kernel schema (one example biz file both repos' tests load).
2. Joint onboarding script: brain creds + voice DID in one session.
3. First live DID → bake-off (pipeline vs S2S) on shared metrics.
4. Second business onboarding → proves multi-tenancy + feed ranking both sides.
