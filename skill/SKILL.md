# VoltLine sparky setup (SKILL.md — paste into Muse Code / Claude skills)

You are onboarding ONE electrician onto VoltLine. Do these in order, verifying each.
Mirror of the whatsapp-shopify-agent SKILL pattern, adapted to voice+trade.

## 1. Profile
- Copy knowledge/tradie_profile.yaml → knowledge/tradie_<name>.yaml; set BUSINESS_CONFIG
  if switching. Fill: base_postcode, phone, prices (RANGES only), max_drive_min,
  mornings_first, enjoys/dislikes. Verify: `python3 -c "from app.tradie import
  load_profile; print(load_profile('knowledge/tradie_<name>.yaml')['tradie'])"`.

## 2. Channels (pick pilot, then scale)
- FASTEST (no approval): QR-gateway pilot (Evolution-style) → forward to POST
  /calls/intake with X-VoltLine-Key. Warn: pilot only, migrate to Cloud API.
- PROPER: WhatsApp Cloud API number (Embedded Signup via BSP, ~5-10 days) →
  webhook → /calls/intake. Voice: SIP trunk (Twilio/Telnyx DID) → LiveKit SIP →
  dispatch `receptionist`-style agent → transcripts → /calls/intake.

## 3. Keys
- `export SPARKY_API_KEYS=<rand>` server-side; sparky app sends X-VoltLine-Key.
  Verify: unauthenticated POST /sparky/act returns 401; keyed returns 200/400.

## 4. Voice (if SIP live)
- QWEN_API_KEY + QWEN_MODEL=qwen-audio-3.0-realtime-plus; first WS message must be
  session.update (see adapters/qwen_omni.session_update_event). Verify handshake in
  dry-run before pointing the DID at it.

## 5. Verify first job (traps to avoid)
- Transcripts land in runtime/cases with triage label? (check /sparky/digest)
- Routine 11pm call does NOT wake (check wake:false)? Safety phrase DOES?
- Booking same idempotency_key twice replays (no double-book)?
- No final price without survey anywhere in draft replies?
- Then: close test cases via /sparky/act close_case; run retention dry-run
  `python3 -m app.retention` and confirm opens are kept.
