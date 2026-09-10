# gentianshero/whatsapp-shopify-agent — clone freely (inspected /tmp/opencode/whatsapp-shopify-agent)

License: **MIT** ✅ — 260-line Cloudflare Worker + SKILL.md + wrangler.toml.

## Why it matters
- No app install: catalog search via the store's own Storefront MCP (`/api/ucp/mcp`,
  post-Aug-2026 endpoint), agent profile URL in `meta.ucp-agent.profile`.
- Flow: WA webhook → Claude agent loop → Storefront MCP search → native WA interactive
  list/checkout button → standard Shopify checkout (cart permalink).
- Ships a Claude Skill that walks setup (Meta dashboard clicks, 4 traps, verify first order).

## Take for us
- The MCP-catalog pattern generalizes: any supplier with an MCP endpoint becomes comparable
  to our parts.py table — live stock instead of stub prices.
- SKILL.md-as-onboarding is the template for our sparky setup ("connect number, verify
  first call" skill for Muse Code/Claude).
- UCP agent-profile hosting: when we expose our jobs/parts API, host our own profile JSON
  the same way so *other* agents (incl. Muse custom connectors) can consume us.
