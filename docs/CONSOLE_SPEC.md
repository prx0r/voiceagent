# Answered Console — product spec (v1, 2026-10-14)

The thing a trade owner lands on. It is not a landing page: it is the product,
pre-loaded with their trade, and an agent that leads them through it one click
at a time. They never have to think of what to type.

## Goals
1. In under 60 seconds an owner has **heard their own receptionist handle a real
   customer** for their trade (role-play or live call).
2. Every step offers **ready-made prompts** (chips) that lead toward: try it →
   see what lands on your phone → see your calendar used → cost → set up.
3. Every feature is reachable from a chip: role-play, live call, calendar,
   website, owner alerts, pricing, system prompt, setup.
4. Claims are **sourced statistics** for their industry (knowledge/stats.json),
   each with publisher and URL. No unsourced numbers in the opening.

Non-goals (v1): writing to a real calendar, real phone numbers, payments, auth.

## Layout (desktop ≥ 900px)
| Area | Contents |
|---|---|
| Top bar | Logo, live price pill, **Start free** |
| Left rail | Trades (electrician … other). Switching trade resets the thread to that trade's opening. |
| Centre | **Thread** (ChatGPT style). Opening message = greeting + 3 stat cards + prompt chips. |
| Composer | Docked pill. Mode switch **Ask Answered / Be the customer**, mic, **Call** button, send. Never scrolls away. |
| Right panel | Tabs: **Website** (customer site iframe), **Calendar** (read-only demo diary), **Your phone** (alerts, digest, callbacks). |

Mobile (< 900px): rail becomes a horizontal strip; right panel opens as a full
sheet from a **Preview** button; thread + composer fill the viewport. The page
itself never scrolls; only the thread does.

## Two agents, one thread
| Mode | Who answers | Endpoint | System prompt |
|---|---|---|---|
| **Ask Answered** (guide) | Answered's onboarding agent, talking to the owner | `POST /api/console/guide` | `app/console.py: guide_prompt(trade)` — trade brief + product facts + stats + calendar; must lead with one next step and never invent numbers |
| **Be the customer** (role-play) | The trade's AI receptionist, as the sample business | `POST /chat` (`trade`) | Trade pack `agent.system_prompt` (knowledge/*.yaml) + calendar context |

Receptionist bubbles are labelled with the business name; the owner's own
bubbles in role-play are labelled "You, as a customer".

## Prompt chips
Every guide reply returns `prompts: [{label, kind, text}]`.

| kind | Effect |
|---|---|
| `roleplay` | Switch to customer mode and send `text` to the receptionist |
| `call` | Open the live call overlay (optionally with an opening line) |
| `guide` | Send `text` to the guide |
| `panel` | Open a right-panel tab (`text` = website \| calendar \| phone) and ask the guide about it |
| `signup` | Open setup form |

Funnel order the guide steers toward: **emergency role-play → normal booking
role-play (uses calendar) → live call → what lands on your phone → cost →
setup**. Chips for steps already done drop out.

## Demo calendar (read-only)
`GET /api/console/calendar?trade=` → next 5 working days, Europe/London.
Deterministic per trade and date (seeded), with booked jobs (customer first name
+ initial, job, area) and free slots. Trade-specific hours and slot lengths
(barber 30 min, MSP 60 min remote, dog walks 60 min blocks, etc.).
The receptionist reads it to offer real free slots ("Tuesday 10:00 or 14:30")
and **never writes**. Booking requests are confirmed as "held, owner confirms".

## Live call
Overlay with business name, timer, speaking/listening state, live transcript,
mute and end. Loop: SpeechRecognition (en-GB) → `/chat` (customer mode, same
session) → speechSynthesis → listen again. Without SpeechRecognition (Safari,
Firefox) the overlay falls back to typed turns, read aloud. Ending the call
posts a summary line into the thread ("Call ended · 1:42 · alert sent to
owner" when urgent).

## Statistics
`knowledge/stats.json`: `{global:[…], <trade>:[…]}`, each `{stat, text, source, url}`.
Opening shows two trade stats and one global stat. Each source is
verified on its page; non-UK figures say so.

## API
- `GET /api/console/{trade}` → `{business, opening, stats, prompts, prompts_text: {guide, receptionist}}`
- `POST /api/console/guide` `{trade, message, session_id?, done?: [kinds]}` → `{answer, prompts, panel?}`
- `GET /api/console/calendar?trade=` → `{tz, read_only:true, days:[{date,label,events,free}]}`
- `POST /chat` (unchanged; now offers free slots from the demo calendar)

## Acceptance checks
- No page scroll at 1440×900 or 390×844; composer always visible.
- Opening for every trade shows 3 sourced stats + ≥4 chips, no emoji.
- Each chip kind works for every trade.
- "Can someone come tomorrow?" in role-play returns real free slots from that trade's calendar.
- Live call works in Chrome; degrades to typed turns elsewhere.
- `node --check` on all inline JS; `/health` ok; `runtime/support.db` untouched.

---

# Offerings, onboarding and lead gen (v1 proposal)

The console is the top of the funnel. Each feature the owner tries in the demo
maps to a product line, and the guide's chips walk them up the ladder.
Prices marked **TBD** are placeholders for the founder to set; the demo never
quotes a TBD price.

## Product ladder
| Tier | What they get | Price |
|---|---|---|
| **Answered** (pay as you go) | After-hours and on-the-job call answering in their cloned voice, instant urgent alerts, 7am digest, callback nags | 50p per active minute, first 10 calls free (live) |
| **Basic** (subscription + tech support) | Everything above plus: **AI-readable website** on their domain, **Google Business Profile** setup and sync, support by WhatsApp | TBD / month |
| **Add-on: WhatsApp agent** | Meta's agent on their WhatsApp for FAQs and bookings; warm/urgent/human handoff to Answered | TBD |
| **Add-on: Agent inbox** | `hello@markelectrician.co.uk` run by the agent: answers enquiries within policy, drafts anything else for approval | TBD |
| **Add-on: Calendar sync** | Real availability from the owner's calendar, privacy-first (below) | TBD |
| **Add-on: Reviews + lead gen** | Review nudges after good jobs; inbound leads from site, GBP, WhatsApp and inbox scored and routed | TBD |

## Basic onboarding (what "set it up for me" does)
1. **20-minute call**: voice clone sample, prices, hours, service area, emergency rules → trade pack (`knowledge/*.yaml` shape).
2. **Number**: divert-on-no-answer code set on their phone, test call together.
3. **Website** generated from the same pack (`/demo/{trade}` template) on their domain or `name.answered.uk`:
   - AI-readable: schema.org `LocalBusiness`/`Service`/`Offer` JSON-LD, `llms.txt`, plain HTML prices and areas, no JS-only content, sitemap, fast static hosting.
   - So ChatGPT, Perplexity and Google AI answers can quote the business correctly.
4. **Google Business Profile**: claim/verify assist, hours, services and prices synced from the pack; booking link → site; messages → agent.
5. **Go live** with a 7-day check-in call; first 10 calls free.

## Agent inbox (custom email)
- Domain: buy or connect theirs; MX via a transactional provider (e.g. Postmark/SES inbound) to `hello@`.
- The agent reads only mail to that address. It answers FAQs, prices and availability from the pack; anything else (complaints, money, contracts) is drafted and sent to the owner to approve.
- Outbound from `hello@` signed "Mark's assistant (AI)". SPF/DKIM/DMARC set at onboarding.

## Calendar sync (privacy rules)
- **Read free/busy only** from the owner's calendar (Google `freeBusy` / Microsoft `getSchedule` / CalDAV free-busy). Never event titles, attendees, locations or notes.
- **Write only to a separate calendar** we create, "Answered bookings". Holds are tentative until the owner taps confirm. We never edit or delete their events.
- Customer PII lives in Answered, not in the owner's personal calendar: the hold shows job type, area and a link, not name or phone.
- Scopes requested are the minimum: `calendar.freebusy` + create a secondary calendar. Revocable any time; revoke deletes our calendar and tokens.
- UK GDPR: we're the processor, the owner is the controller. DPA at signup, transcripts kept 90 days by default, export/delete on request, call recording announced.

## Lead generation loop
Every channel (calls, site chat, GBP messages, WhatsApp, inbox) writes the same
**lead record**: source, trade, job, area, urgency, value band, status. That gives us:
- The owner's lead list and conversion in the 7am digest.
- Overflow routing (opt-in): jobs the owner can't take go to vetted partner trades in the area, for a referral fee. Owners join as givers and takers.
- Anonymised, aggregated trade stats (missed-call rates, after-hours share) for marketing, never individual data.

## Console mapping (chips → product)
| Chip | Shows | Upsell |
|---|---|---|
| Be my customer (emergency/booking) | Receptionist | Answered |
| Ring it live | Voice | Answered |
| How does it use my diary? | Diary tab | Calendar sync |
| What do my customers see? | Website tab | Basic (website + GBP) |
| What about WhatsApp and email? | Plans tab | WhatsApp agent, Agent inbox |
| What would it cost me? | Plans tab | Ladder |
| Set it up for me | Setup form | Lead captured (`/api/callback`) |
