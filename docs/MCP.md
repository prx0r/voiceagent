# MCP — future agentic surface (PLANNED, not built)

Goal: any MCP client operates the voice lane natively (like cg's `cogym_kernel.mcp`):
same kernel, same gates, receipts as proof. HTTP API + UCP profile are the interim
contract (docs/CONNECT.md, static/ucp/profile.json).

## Planned tools (thin over existing endpoints — no new logic)
| Tool | Args | Returns | Maps to |
|---|---|---|---|
| `qualify_lead` | postcode, photos, charger | score, missing, next | evtools |
| `book_survey` | name, phone, postcode, slot, idempotency_key | booking_id, case_id (replays) | funnel/book |
| `intake_call` | transcript + meta | level, draft, slots, worth_it | afterhours |
| `sparky_digest` | — | queue + catch report | digest |
| `sparky_act` | case_id, action, … | receipts | act (approval-gated) |
| `job_feed` | — | ranked jobs | feed |
| `run_night_sim` | — | 8-scenario verdicts | simulate_calls |

## Rules (mirror cg's MCP doctrine)
- Tools thin over kernel surface: same determinism, same gates, same receipts.
- Approval-gated actions stay gated over MCP (no backdoor autonomy level).
- Every call audited; evidence digests pinned like csec records.
- Transport: stdio first (`python3 -m app.mcp.server`), streamable-http when hosted.

## Adding a tool (when built)
1. Entry in `app/mcp/server.py:TOOLS`. 2. Handler calling the kernel function.
3. Test round-tripping the tool in `tests/test_mcp_stdio.py`. 4. Row in the table above.
