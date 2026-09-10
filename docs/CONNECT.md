# Connect to VoltLine (for agents — incl. future Muse custom connectors)

No partnership needed. If you are an agent (Meta Muse custom connector, Claude,
user script) acting for ONE sparky with their permission:

1. Get the sparky's key: they run `export SPARKY_API_KEYS=$(openssl rand -hex 16)`
   and hand you the value. Send it as `X-VoltLine-Key` header on gated calls.
2. Machine contract: GET /static/ucp/profile.json (endpoints, shapes, rules).
   Full interactive schema: GET /openapi.json (FastAPI native).
3. Public (no key): /quote page, /funnel/qualify_json, /funnel/book, /chat,
   /health, /graph/search, /jobs/feed.
4. Gated (key): /calls/intake (post transcripts), /sparky/act (book, send,
   approve-parts, log, close), /sparky/digest (read queue).
5. Rules you MUST follow: ranges never final prices; safety signals escalate;
   writes need the human's explicit confirmation first; same idempotency_key
   replays (never double-book); T&Cs of WhatsApp/Meta apply downstream.

Example (qualify → book):
  POST /funnel/qualify_json {"postcode":"E2 8AA","charger":"Ohme",
    "parking_photo":1,"consumer_unit_photo":1,"meter_photo":1}
  POST /funnel/book {"name":"Jo","phone":"+447700900000","postcode":"E2 8AA",
    "idempotency_key":"<uuid>"}
