# TailorTalk — brief (source: tailortalk.ai/integration/shopify, fetched 2026-09-10)

India (Bangalore). Meta Partner, Google for Startups. G2 4.9, Trustpilot 5/5.
Positioning: pre-purchase SELLING agent (vs Gorgias-style post-purchase helpdesk).

## What it does
- One agent, one config, shared memory across WhatsApp + Instagram DMs + website chat.
- Live Shopify catalog at answer time (sizes/colours/prices, never cached).
- Photo-to-product matching (screenshot/reel frame → closest in-stock item).
- Guided selling → payment link in-thread (Stripe/Razorpay/PayPal), no redirect to site.
- Order tracking/support against real Shopify order data; human handoff when unsure.
- Abandoned-cart recovery on WhatsApp (only to people who already messaged — no cold
  recovery for unknown abandoners; stated plainly as the trade-off).
- Order/delivery updates + review requests triggered by Shopify webhooks (order,
  fulfilment, checkout events). ~30-min setup, no code.
- Extra agents: AI catalog builder (photo→structured visual catalog), WhatsApp
  re-engagement campaigns with AI follow-up/close.

## Key platform constraint (best articulation of the six)
- WhatsApp: merchant-initiated OK (phone number maps to identity) → updates/recovery work.
- Instagram: reply-only, no order→account bridge → NO outbound updates possible. IG = inbound
  photo selling → payment link, or move customer to WhatsApp. "No tool can work around it."
- Number-quality safety: only messages existing conversations, never cold broadcasts.

## Tech pattern to steal
Shopify API + webhooks → event router → Cloud API send; inbound agent reads live stock per
reply; shared conversation memory keyed across channels; RAG over catalog+policies.
Alternatives pages (vs Gorgias/Tidio/Intercom/Chatfuel) = good objection-handling swipe file.
