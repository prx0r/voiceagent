# AI-agent access (MCP) and per-trade site purpose

## Navigation (10-14)
- `/`: trade grid (static/home.html). One card per trade.
- `/t/{trade}`: that trade's console (static/app.html), locked to one business. There's no trade switcher, only "All trades" back to `/`.
- Left sidebar is the owner's menu, not a trade list:
  - **Be a customer**: 5 trade-specific scenarios (`SITE[trade].scenarios` in app/console.py) plus *Ring it live*.
  - **Your business**: Your website, Diary, Alerts and leads (badge counts urgent alerts), AI agents, Plans, Instructions.
  - **Get it**: Set it up for me.
- Mobile: the sidebar is hidden. The chips and the Preview sheet cover the same actions.

## Why people visit each trade's site
The site and agent are built around the reason someone lands there. This drives the customer site, the agent prompt and the MCP tools. Source: `SITE` in app/console.py, shown in the AI agents panel.

| Trade | Top visit reasons | Site and agent must |
|---|---|---|
| Electrician | sparking or tripping now; EV/rewire price; EICR; proof of registration | 24/7 emergency line, guide prices, NICEIC/NAPIT badges, survey booking |
| Plumber | leak now; fix this week; price first; postcode covered | stopcock advice, callout fee up front, postcode areas, diary booking |
| Heating | no heat; annual service; new boiler; Gas Safe proof | gas safety first, service booking, Gas Safe number, quote with photos |
| Locksmith | locked out now; ETA; price; locks after move or break-in | one-tap lockout with ETA, day and night prices, DBS badges |
| Beauty | book without ringing; prices and durations; patch tests; reschedule | online booking, price list, patch-test rules, deposit policy |
| Barber | chair free now?; book today; prices; move a booking | live free slots, two-tap booking, walk-in rules, no-show reminders |
| Dog walker | space for a new dog?; prices; insured/DBS?; change a walk | meet-and-greet booking, areas, badges, walk updates |
| IT/MSP | outage now; raise ticket; per-user quote; new starter | P1 paging, ticket intake, SLA pricing, status page |
| Sole trader | can you do it?; rough price; when free; local and reliable? | quote form with photos, guide prices, quote-visit booking, reviews |

## MCP server (one per business)
`POST /mcp/{trade}`: MCP over Streamable HTTP, JSON-RPC 2.0, stateless, JSON responses, protocol `2025-06-18`. `GET` returns a descriptor (405 for an SSE Accept). CORS is open.
Implementation: `app/mcp.py` (no extra dependencies). Requests are logged to `var/mcp_requests.jsonl` (gitignored).

| Tool | Kind | Notes |
|---|---|---|
| `get_business_info` | read | hours, area, emergency and booking policy, channels |
| `list_services` | read | guide prices in GBP, optional query |
| `check_availability` | read | free slots only (date, part_of_day, limit). Never shows event content or other customers. Held slots are hidden |
| `request_booking` | write-request | needs name and a UK phone, and the slot must be free. Returns `hold_id` with `pending_owner_confirmation`. The owner confirms by text |
| `report_emergency` | write-request | returns the trade's safety advice first. Jev triage decides between `on_call_alerted` and `logged_for_morning` (alerts if triage is unavailable) |
| `leave_message` | write-request | goes to the 7am digest |

The same rules as the phone line: nothing is confirmed, cancelled or charged by an agent; no PII about other customers; owner confirmation on anything binding.

### Connect
- **ChatGPT**: Settings → Apps & Connectors → Advanced settings → Developer mode, then Create connector, then paste `https://<host>/mcp/<trade>` (no auth in the demo).
- **Claude**: Settings → Connectors → Add custom connector, using the same URL.
- **Test**: `npx @modelcontextprotocol/inspector`, or curl `{"jsonrpc":"2.0","id":1,"method":"tools/list"}`.

## Next
1. **Auth for real businesses**: OAuth 2.1 (MCP authorization spec) per business, scoped `read` vs `request`. Rate limits per client.
2. **Agent-to-agent negotiation**: add `propose_alternatives` (the agent sends constraints, the server returns ranked slots) and `quote_request` (with photos as resource links). Keep "owner confirms" as the commit step.
3. **Discovery**: the customer site advertises the MCP URL in JSON-LD (`potentialAction` / ReserveAction) and in `llms.txt`, so assistants find it from the website.
4. **Real holds**: write tentative events to the separate "Answered bookings" calendar (see CONSOLE_SPEC calendar privacy). Hold expiry after 2 hours.
5. Lead records from MCP join the same lead pipeline as calls, WhatsApp and the inbox.
