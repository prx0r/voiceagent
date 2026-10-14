# ONBOARDING SPEC — pay-as-you-go, no subscription, no bullshit.
# Human tech support on demand (setup call + WhatsApp), AI handles the rest.

## Commercials (say it exactly like this)
- 50p per active minute. Timed from answer to hangup, rounded up.
- No subscription. No retainer. No minimum. First 10 calls free.
- Human help: free on the setup call, then on demand at need (fair use).
- Cancel by text. Number released same day. Knowledge exported on request.

## Stage 0 — gap audit (before they pay anything, free)
Run from our side, results in the outreach email:
1. Google profile check (SerpApi Maps: listed? hours? 24/7 flag? photos?
   rating + count + recency + replies?). Needs SERPAPI_KEY on our box.
2. Directories (Checkatrade/Yell/TrustATrader) + trade body (NICEIC/Gas Safe).
3. Reviews scan (count <20, stale quarter, unanswered negatives = gaps).
4. After-hours test (public hours say closed + no answering service = leak).
Output: "you're missing X, that's ~£Y/mo walking past" + demo link.

## Stage 1 — setup call (20 min, screen-share, free)
Collect (nothing technical asked of them):
- trade, business + owner names, work number, owner mobile, digest email, WhatsApp
- hours, area, price bands, the 5 FAQs, logo file
- 10s+ donor voice clip (owner reads anything clearly)
We do live: pack copy filled, voice cloned + greeting previewed, divert code
set + test-rung twice, WhatsApp basics, Meta agent only if eligible+wanted.
Env on our box per client: BUSINESS_CONFIG=knowledge/[slug].yaml.

## Stage 2 — first week (free 10 calls)
- Out-of-hours live. Emergencies SMS+WhatsApp instantly, rest 7am digest.
- Callbacks nagged every 2h. Owner marks done.
- Friday review: minutes used, qualification rate, any mishandle, one quote.
- Then: meter starts. Invoice monthly from runtime/calls.jsonl totals.

## Stage 3 — expand (their call, our menu)
- Bookings + calendar, review engine, no-show chasers, win-backs.
- WhatsApp two-way (Meta agent configured, handoff to us).
- Extra numbers / vans / branches. Training sim for staff.
- Custom consulting (dispatch, landlord contracts). Day rate, waitlist.

## Kill rules
- Mishandled emergency or invented price: stop, read logs, fix guard, re-test.
- 200 outreach touches <5 trials: message wrong. Trials stalling: demo quality.
- Client under 10 min/mo for 3 months: keep (margin fine) but send the
  monthly "jobs we caught" email or they forget why they stay.

## Prior art inside our estate (use, don't rebuild)
- aionboard GO_TO_MARKET.md: Maps scraping playbook (Vonsel/StreetLead),
  "52% unmatchable = sole traders = our market".
- aionboard data/prospects: 10k electrical + Manchester lists (SerpApi +
  Companies House enriched). STUBSEARCH.md: honest audit of what's REAL.
- aionboard GEO_OPPORTUNITIES.md: powuk signals for where demand outstrips cover.
- cgraphuk campaigns: 24 vertical briefs. ographuk: opportunity pipeline.
