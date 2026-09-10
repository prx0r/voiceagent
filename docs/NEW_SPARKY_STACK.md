# The New Sparky Stack — ChatGPT-native, so we don't rebuild ChatGPT

Principle: if ChatGPT + phone camera already does it, we don't build it.
We build what needs business state, phone line, money, or certificates.

## What ChatGPT already covers (do NOT build)
- Photo diagnosis chat ("what breaker is this?")
- Generic advice (7kW vs 22kW explainer, Ohme vs Easee pros/cons)
- Drafting quotes/emails/complaint responses
- Explaining regs in plain English
- Sparky studies for exams (18th edition revision)

## The stack (in acquisition order)

### 1. ACQUIRE — free EV leads (the wedge)
- EV quote funnel: postcode + 3 photos → qualified survey booking.
- Tool: `qualify_lead` scores 0-100, lists missing photos.
- Why they take it: junior sparkies have no reputation, no Checkatrade rank.
  Free charger jobs > any feature pitch.
- Cost to you: keep it to ONE job type (domestic 7kW) + ONE geo to start.

### 2. KEEP — after-hours call catcher (the retainer)
- Missed calls = lost jobs. Agent answers 24/7, wakes engineer only if urgent.
- Tool: `triage_urgency` — safety signal or (dead charger + vulnerable) = wake_now,
  else next-working-day ticket. Conservative by design.
- Voice: Qwen3.5-Omni realtime (`adapters/qwen_omni.py`) for barge-in + natural
  talk, same graph/guard kernel underneath. Edge TTS stays as dev fallback.
- Price: flat/mo per sparky, easy ROI math (1 saved job pays for quarter).

### 3. EXPAND — admin they hate
- Remote survey booking with idempotency (`book_survey` — retries replay receipt).
- Ticket/callback log (`create_support_ticket`, `request_callback`) — every call
  becomes a case with photos attached, survives phone→van→office.
- DNO + cert pack: EIC, Part P, DNO notify templates prefilled from survey.
  (Templates + reminders, not legal advice.)

### 4. LOCK-IN — money
- Quotes from survey (ranges → fixed after visit), deposits, invoices, reminders.
- Only now: you hold their cashflow. Churn drops to ~zero.
- Later: van stock (breakers, CT clamps, mini boards), supplier pricing via graph.

## Middleman flow (EV consumer → sparky)
```
EV driver (needs charger) → quote funnel → qualify_lead ≥80
  → book_survey → sparky does install → cert/DNO → review back to funnel
       ↓ <80                       ↓ fault at 11pm
  ask for missing photos      triage_urgency → wake or ticket
```
The graph (`knowledge/ev_charger_install_en.yaml`) is the shared truth:
chargers × eligibility × pricing ranges × grants × safety. Compiles to voice,
web chat, and quote funnel without re-entry.

## What to measure (first 10 sparkies)
- Answer rate after hours (target >95%)
- Qualify→survey conversion (target >40%)
- False wake rate (target <1/week/sparky — else they mute you)
- Jobs/sparky/month from funnel (target ≥4 to justify retainer)

## Explicit non-goals
- No generic chatbot, no photo identifier, no exam tutor.
- No final price without survey. No grant guarantee. No remote safety diagnosis.
- No three-phase promise without DNO check.
