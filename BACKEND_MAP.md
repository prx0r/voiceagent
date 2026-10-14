# BACKEND MAP — where everything lives and how clients stay separate.

## Repo roles (don't duplicate across these)
| Repo | Role | We touch |
|------|------|----------|
| voiceagent (here) | Product core: packs, policy graph, afterhours flow, adapters, site + demos, Meta bridge | daily |
| aionboard | GTM: prospects, outreach copy, GEO signals, website generator (standard tier) | outreach days |
| cgraphuk | Reference graph (templates/pains/campaigns/profiles). Read-only mirror; edit voiceagent, port back rarely | read |
| ographuk | Oracle runtime -> Seesaw econ eval (which trade/postcode next) | read |
| influence/dash | Ops console: stonedoorway foundry, Fish voices/clones, review canvas | ops |
| figgsite | Oddhobb consumer world. Sibling only — never product logic here | never |

## Per-client convention (this repo)
- One pack per client: `knowledge/[slug].yaml` (copy the trade template, fill brackets).
- Everything namespaced by `business` slug: reminders, outbox, calls ledger,
  bookings rows all carry it. Filter with `ledger_totals(slug)`.
- Runtime identity: `BUSINESS_SLUG` env. One process per client (PORT per client),
  or single process with slug passed per call. Start single; split at ~20 clients.
- Secrets per process env, never in packs: FISH_API_KEY, FISH_VOICE_ID,
  GMAIL_USER/APP_PASS, TELNYX_API_KEY/FROM, WHATSAPP_*, META_SUAT/PHONE_ID,
  DASHBOARD_TOKEN, RATE_PER_MIN_GBP.
- No cross-client reads: ledger/reminder queries always filter by slug.
  The `/api/*` demo endpoints take `business` slug per request.

## Production posture: TEE AI
Live customer traffic runs in trusted execution (TEE AI): caller PII never
trains vendor models, per-call keys sealed, audit receipts per action.
Contributor-tier brains (anything that trains on prompts) stay on OUR side
only — evals, scoring, rehearsal — never on customer calls. Local Ollama or
zero-retention endpoints for anything a caller says.

## Data flow (one call)
```
divert/PSTN (Telnyx) or browser demo or Meta handoff
  -> intake (pack script + policy graph states)
  -> classify (emergency? complaint? standard?)
  -> emergency: SMS owner + backup, WhatsApp ping
  -> digest email (Gmail) + transcript + recommendation
  -> reminder queued (2h nag) + ledger row (50p/min)
  -> morning review: ledger totals + qualification rate
```

## Website tiers (from template research, not cloned)
Reference templates per trade (structures pinched, code ours — ours is wired
to /api + booking, theirs isn't):
- plumber/heating/electrician: TwoSquaresHQ plumber-services-starter (lead-gen
  structure), MSMITH71910 plumber 5-pager (emergency page + chatbot pattern),
  bso-batiment (multi-trade FR, MIT), themewagon/Plumberz (MIT).
- barber/salon: Rak-Code/BlaXcut (MIT), technext/Salon, FAANG-star/Salon-voice-agent
  (full-stack reference: strict booking order, phone readback in pairs, end-of-call SMS).
- dog walker: bbeare22/millies-pet-service (MIT: services/pricing/policies/gallery/reviews),
  tranmh/gassigeher (SaaS subdomain multitenancy pattern — our xyz.aionboard.co.uk model).
- whatsapp: Hiberius/whatsapp-receptionist (MIT, 360dialog BSP path for phase 2).
Required sections per trade site: services+pricing, emergency page/CTA,
reviews, policies (patch/no-show/meet-greet), gallery, booking widget,
click-to-WhatsApp. Ours already has all seven via demo_template + packs.
