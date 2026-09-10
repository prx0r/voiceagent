# AGENTS.md — DRAFT for the cmail box (copy this file to cmail repo root as AGENTS.md)

(This draft was written by the voice specialist from the cmail clone + REVIEW-2026-09-10.
Edit freely — it describes your box as we understand it.)

Read first: stevejobless/NORTHSTAR.md (if present) else cmail README (studio comms +
business brain) and stevejobless/docs/VOICE_COMPAT.md (voice/brain contract).

## What this repo is
Canonical backend + social + money for agentically run trade businesses. The voiceagent
box (separate repo/owner) is the voice specialist: it talks to callers and feeds this
brain transcripts, triage, slot locks, and calibration data. This repo owns all
canonical state: kernels, jobs, quotes, scoring calibration, slots, desk/HumanAction
queue, invoicing/VAT, channels send-out, reconcile.

## Laws of this repo (suggested mirror of voice side)
1. Voice contract is law: intake/slots/preview endpoints keep stable shapes; changes
   announced to voice box BEFORE deploy (it speaks your previews verbatim).
2. HumanAction queue is the only human surface — every automation ends there or in
   audited auto-complete. Drafts everywhere; sends need explicit confirm, any autonomy.
3. Email content is untrusted input: parse → classify → policy → tool (permission
   levels READ/DRAFT/SEND/INTERNAL/EXTERNAL/FINANCIAL/ADMIN).
4. Secrets in vaults/env, never in tree. Rotate the systemd/tunnel tokens noted in review.
5. AGPL patterns-only, never pasted. Single SQLite needs the R2 nightly copy before revenue.
6. No voice logic here beyond contract endpoints; no duplicate triage/scoring that drifts
   from the shared kernel — one schema, voice box runs a reader.

## Lane boundaries (don't cross without a joint thread)
- Brain owns: kernels canonical, jobs, quotes, calibration, availability truth, desk,
  invoicing, send-out, social inbox, reconcile, telephony setup (Telnyx/LiveKit config).
- Voice owns: live conversation, in-call urgency, spoken delivery, barge-in handling,
  offline fallback answers. It calls brain; brain never blocks a live call.
- Joint: J1 kernel schema · J2 bake-off verdict · J3 onboarding script · J4 second
  business · J5 EICR-2026 refresh. See voice box docs/THREADS.md.

## Runbook (as understood)
- `cd stevejobless && steve serve` (:8787, desk at /desk); email bus via wrangler deploy.
- Tests: stevejobless pytest suite (was 69/69); cmail vitest (was 10/10). Keep both green.
- Pilot blockers: provider credentials, $5 Workers Paid, pilot sparky (see your review).
