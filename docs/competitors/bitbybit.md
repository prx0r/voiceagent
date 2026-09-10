# bitbybit — brief (source: bitbybit.studio/shopify, fetched 2026-09-10)

Strongest of the six. Official Shopify Partner + Official Meta Tech Partner. 1,000+ brands,
50+ countries, 100+ languages. Suite: bitChat 4.7★ / bitCRM 4.3★ / AI Studio / bitApp /
bitLink / bitLoyalty(beta) / bitLogin. Free plans, no card.

## Architecture (the one to study)
- ONE customer record + ONE agent across every app. Every Shopify action enriches the same
  profile; broadcasts read it; agent answers from it. Install one app → works; add more →
  compounding context.
- Shopify stays source of truth: OAuth install; products/variants sync; inventory+price read
  LIVE per answer (never cached snapshot); tags/custom fields/metafields sync both ways;
  browsing signals via existing Shopify pixel; review requests (Stamped/Yotpo) over WhatsApp;
  orders created in-thread, written back to Shopify admin.
- Deepest event hooks: native Shopify trigger family (abandoned cart/checkout, order
  created/unpaid/paid/fulfilled) + Shopify Flow step. Payments = own in-thread links
  (Xendit/DOKU), NOT Shopify checkout.
- Escalation guardrail demo: wholesale-price ask → "I won't guess, bringing in our team"
  with full thread. Guardrails + pre-live playground (test as returner/first-timer/hunter).
- Funnel that converts: bitLink (shoppable link-in-bio on own domain) → bitLogin (social/WA
  OTP sign-in, tag write-back) → bitChat (agent w/ context) → bitCRM (cart recovery) →
  bitApp push (no Meta per-message fee — "cheapest reach you own") + loyalty in-thread.
- Messaging economics: WA conversation fees passed through at Meta rates, NO markup; flat
  platform fee. Trust-builder worth copying.

## Gaps (our opening)
100% retail/Shopify-shaped. No voice calls/PSTN, no services calendar, no per-job
scoring, no tradevertical (certs, DNO, quotes-from-photos, after-hours wake logic).
Their "one record" = our case file; their playground = our eval_text.py.
