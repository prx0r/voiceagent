# Workflows: AgentRun + Jev + the LLM backend

## Split of responsibilities
| Layer | Does | Where |
|---|---|---|
| **Jev** (TypeSafe System One, via OpenRouter) | Typed decisions with probabilities: intent, urgent?, vulnerable?, spam? About 0.2 s and about $0.00002 a call | `POST https://openrouter.ai/api/v1/systemone`, model `jev-1.13` |
| **AgentRun DSL** | Control flow you can inspect: judge → escalate if unsure → code policy → route. Workflows are JSON files, validated offline | `workflows/*.json`, `@parcha/agentrun-dsl` |
| **LLM backend** (Pi/OpenCode through `LLM_*`) | Generates the words: replies, summaries, digests. Never decides policy | `app/llm.py` |
| **Python app** | Tools, the diary, alerts, storage. Owns every side effect | `app/main.py` |

Rule: **Jev decides, code enforces, the LLM speaks.** Policy thresholds live in code nodes, so a model can't talk its way past them.

## Setup
- `.env` (gitignored, chmod 600): `OPENROUTER_API_KEY`, `TYPESAFE_API_KEY` (same key), `TYPESAFE_BASE_URL=https://openrouter.ai/api`.
- `cd workflows && npm install` (Node ≥ 22.19).
- Check: `npx agentrun validate call-triage.json --trusted`
- Run: `echo '{"trade":"plumber","business":"X","message":"pipe burst"}' | node triage.mjs`
- `app/workflows.py` shells out to it with a 6 s timeout and a 10-minute cache. Without node, the packages or a key, it returns `None` and the regex/rules path takes over.

## Live now: `call-triage` (every trade)
Input `{trade, business, message, local_time}` → Jev judges `intent` (emergency, booking, reschedule, price, complaint, existing_job, other), `urgent`, `safety_advice`, `vulnerable`, `wants_human` and `spam`. It escalates if intent confidence < 0.55. Then code policy → `action` (alert_owner_now, offer_slots, check_diary, give_price, reschedule, take_message, drop_spam) plus a priority.
`/chat` returns `triage` and the console shows it under each receptionist reply.
Eval, 11 cases across 9 trades: all routed correctly. Latency is 210–270 ms.

## Workflow backlog (most value first)
1. **After-call wrap-up**: extract (LLM) name, phone, address, job → Jev sanity-checks it ("is this a real UK postcode / phone?") → owner SMS for P1, digest line otherwise. Replaces the regex alert text.
2. **Callback nagger**: every 2 h, Jev judges each open lead (`still_needs_callback?`, `customer_angry?`) from the latest messages → reminder, or mark done.
3. **Review gate**: after a job, Jev scores sentiment (1–5 rubric). 4 or 5 → Google review link. 1 to 3 → private "how can we fix it" to the owner. Stops bad public reviews.
4. **Booking guard**: before holding a slot, Jev checks the service matches the slot length and the area is inside the service radius; code checks the diary. Anything unsure gets a human confirm.
5. **Agent inbox triage** (`hello@domain`): the same call-triage plus `needs_reply`, `has_attachment_photo`, `is_quote_request`. Auto-replies only when FAQ or price confidence ≥ 0.9; everything else is drafted for approval.
6. **Lead scoring / overflow**: Jev `pick` chooses the best partner trade for overflow by area and speciality, with an explicit "none" option. Opt-in referral.
7. **Safety verifier**: before any emergency reply ships, Jev checks that it contains the trade's required safety line (gas → 0800 111 999, electrics → isolate). If not, swap in the canned safety text.
8. **Onboarding interviewer**: the guide's conversation goes into an LLM extract of a pack draft (prices, hours, areas), and Jev flags missing or contradictory fields to ask about next. This is how "set it up for me" becomes self-serve.
9. **Training simulator scorer**: staff role-play is scored by Jev rubrics (empathy, safety first, captured details) for the training add-on.
10. **Cost cascade**: a cheap LLM drafts, Jev verifies "does this answer the question using only the evidence?" (OpenRouter's Jev-verified cascade), and it escalates to a bigger model only when needed.

## MVP recommendation
Keep it to **three workflows**, all universal across trades:
`call-triage` (done) → `after-call-wrapup` → `review-gate`.
Together they cover the paid promise (urgent alerts and the morning digest) and the first upsell (reviews). Everything else waits until real call volume shows where the errors are.
Per-trade differences stay in the trade pack (`knowledge/*.yaml`) and in the `trade` field of Jev's state, not in separate workflows.

## Guardrails
- Credentials only in `.env` or the vault, never in workflows, the browser or git.
- Jev probabilities aren't calibrated guarantees. Thresholds are tested on fixed cases in `workflows/` before they change behaviour.
- Workflows never send or spend: they return an `action`, and the Python host does it with its own rules (owner confirm on anything binding).
