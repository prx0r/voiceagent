# RUNBOOK — first UK pilot (one electrician, one week)

Goal: one paying sparky + proof the loop holds. Nothing here needs permission
beyond the owner's yes.

## Day 0 — setup call (20 min, screen-share)
1. Copy `knowledge/trades_soletrader_uk.yaml` -> `knowledge/[slug].yaml`, fill brackets.
2. Clone owner voice: 10s+ clean audio -> dash clone flow -> paste voice id into pack.
3. Set packs's launch contacts (mobile, digest email, WhatsApp).
4. Set divert: no-answer 15-20s to their Telnyx number. Test-ring it twice.
5. WhatsApp: business app basics (profile, away message pointing at calls).
   Meta agent only if eligible + wanted — else skip, calls first.
6. Env on the box: FISH_API_KEY, GMAIL_USER + GMAIL_APP_PASS, TELNYX_API_KEY +
   TELNYX_FROM, WHATSAPP_* only when phase 2 starts, RATE_PER_MIN_GBP=0.50.

## Day 1-7 — live
- Agent answers out-of-hours. Emergencies SMS+WhatsApp instantly, rest by 7am digest.
- Owner marks callbacks done; reminders nag every 2h until then.
- `scripts/remind.py --once` on cron every 30 min.
- Review Friday: ledger totals (calls x mins x £0.50), qualification rate,
  any complaint, one owner quote for the site.

## Kill/continue
- Zero emergencies mishandled + owner happy = continue to sparkies 2-5.
- Any invented price or missed emergency = stop, read the logs, fix the guard.
- 30 days: answer rate up, reviews clean, first £20-40 invoice paid = pilot proven.
