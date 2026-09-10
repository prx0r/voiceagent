# eGrow — brief (source: apps.shopify.com/egrow-1, fetched 2026-09-10)

By Safe Apps (Marrakech). Launched May 2026, 5.0★ (3 reviews, thin). COD/Morocco skew.

## What it does
- No-code workflow automation builder (Shopify ↔ WhatsApp/Instagram/shipping/email/ads)
  + built-in AI agent: replies on WA/IG 24/7, handles voice notes/images/calls (not just text),
  30+ languages, creates/confirms/dispatches orders from conversation.
- Data access requested: customers, products, inventory, draft orders, fulfilments — i.e.
  full order-write scope.

## Pricing (platform + usage, USD, billed 30d)
- $59/mo: 1k orders, 4 users, 10k automation credits, 3 WA numbers.
- $99/mo: 5k orders, 9 users, 50k credits, 6 WA numbers, standard API.
- $199/mo: 20k orders, 20 users, 100k credits, 9 WA numbers, advanced API.
- Add-ons for users/numbers/workspaces; credits/messages/AI replies metered.

## Tech pattern to steal
Automation-credits metering (workflow runs + AI replies as one unit); voice-note/image/call
input as first-class (closest to our Qwen-voice wedge); order-write via draft orders.
Watch: review base is tiny; COD-market fit may not transfer to UK trades.
