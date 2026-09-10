# kirklandsig/AIReceptionist — THE voice clone target (inspected /tmp/opencode/AIReceptionist)

License: **AGPL-3.0** — learn from it, do NOT paste code into a closed product.
Fork-or-cleanroom only. 137 files, Python, LiveKit Agents SDK + OpenAI Realtime.

## What it already solves (our roadmap items, done)
- LiveKit AgentServer/AgentSession speech-to-speech loop, noise cancellation (BVC Telephony)
- SIP in/out (Twilio/Telnyx), transfers (incl. Asterisk tel: vs sip: URI fix), REFER
- YAML per-business config, multi-business from one agent process
- booking/ (availability.find_slots, SlotProposal, Google cal setup + CLI), messaging/
  dispatcher, intakes/ (DTMF capture for gate codes etc.), lifecycle, recording+egress,
  transcript capture/format/write, email (Resend/SMTP + summarizer + templates),
  retention sweeper, restart launcher, tests/ incl. transfer/lifecycle/intakes/email
- After-hours detection with configurable messages; pydantic everywhere

## Port plan (patterns → our kernel, no AGPL paste)
1. booking/availability.find_slots + SlotProposal → replace our tools/calendar.py stub.
2. intakes/ lifecycle (open→capture→confirm→close) → harden our /calls/intake + cases.
3. transcript/ (capture+format+writer+metadata) → our digest transcripts.
4. messaging/dispatcher → our whatsapp.py send path.
5. retention/sweeper → runtime/ hygiene (GDPR story for sparky customer data).
6. tests/intakes/* → model for our test_sparky.py growth.
Swap point: agent.py builds OpenAI RealtimeModel kwargs — mirror that seam for Qwen
realtime (our adapters/qwen_omni.py) so the brain stays model-swappable.
