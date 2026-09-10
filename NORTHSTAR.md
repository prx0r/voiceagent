# NORTHSTAR — the agentically run business (voiceagent lane)

## Vision (one paragraph)
A one-person trade business run by an agent: the agent sets itself up (brain +
backend + social, canonical in `prx0r/cmail`), and talks to real people through
voice (this repo, the specialist). Every call, message, job, quote, invoice and
review flows through one system with one human queue. The human does the skilled
work; the agent does everything around it.

## Division of labour (locked)
- **cmail/stevejobless (canonical):** setup/orchestration, business brain (kernels,
  jobs, quotes, scoring calibration), backends (Telnyx/LiveKit config, Google
  Calendar, WhatsApp/IG/SMS/email send-out), desk UI + HumanAction queue, invoicing/
  VAT, reconcile, social inbox→lead. Source of truth for business state.
- **voiceagent (this repo, specialist):** real-time voice interaction with callers —
  ears, mouth, turn-taking, in-call urgency judgement, spoken quote delivery — and the
  feedback it sends back: transcripts, triage, slot locks, spoken-quote receipts,
  worth signals, barge-in/interruption data. Never holds canonical state; never sends
  outside voice without the brain; degrades to local kernel offline, syncs on return.

## How voice affects the rest of the stack (the specialist's obligations)
1. Every call opens/updates a brain Job with transcript + triage (voice→intake).
2. Spoken slots come from brain availability; locks confirm back (no phantom bookings).
3. Spoken quotes are brain previews, verbatim-or-"provisional" (no invented prices).
4. Interruptions/escalations land in the HumanAction queue with full context.
5. Call outcomes train scoring (worth-it calibration) and the EICR/reminder engine.
6. Voice metrics (answer rate, bake-off latency, verdict accuracy) report to the desk.

## Non-goals for this repo
No send-out channels, no invoicing, no canonical jobs DB, no social inbox, no S2S
religion — pipeline first, bake-off decides, seams stay open.
