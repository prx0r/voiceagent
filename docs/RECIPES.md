# RECIPES — copy-paste operations

## Run the server
```bash
pip install -r requirements.txt && cp .env.example .env   # first time only
./scripts/run.sh                       # → http://localhost:8080
BUSINESS_CONFIG=knowledge/ev_charger_install_en.yaml ./scripts/run.sh   # sparky mode
```

## Verify everything (gates — run before every commit)
```bash
python3 -m pytest tests/ -q            # expect 39 passed
python3 scripts/simulate_calls.py      # expect 8/8
python3 scripts/e2e_kernel.py          # expect 15/15
python3 scripts/eval_transcripts.py    # expect 40 routine (drift check)
```

## Onboard a sparky (15 min — full checklist in skill/SKILL.md)
1. Copy `knowledge/tradie_profile.yaml`, fill prices (RANGES), prefs, scheme ID.
2. Pick `answer_mode`: `missed_only` first (forward `*61*<DID>*20#`), graduate later.
3. `SPARKY_API_KEYS=$(openssl rand -hex 16)` → app sends `X-VoltLine-Key`.
4. Test call → check `/sparky` digest → close test cases → retention dry-run.

## Add a business vertical (no code)
Copy `knowledge/ev_charger_install_en.yaml`: business/agent/voice blocks + nodes
(policies, services, products, faqs, escalations) + edges. Retrieval + guard + funnel
work unchanged. Add retrieval test in `tests/test_ev_charger.py` style.

## Add a red-team probe (csec repo consumes these)
Append to the pack with id/class/industry/uk_ref/vector + grade lists; run
`pytest tests/ -q` (schema) then live `BASE=... python3 -m csec.runner`.

## Bake off a TTS voice (protocol in docs/TTS_BAKEOFF.md)
Same 10 utterances × each voice → blind rank + P95 first-audio + £/1K chars →
pin winner in `TTS_PROVIDER`, loser stays fallback. Never decide from spec sheets.

## Cut over a phone number (live calls)
Telnyx no-code assistant first ($20 credits) → DID → dispatch to `livekit_agent/` →
test off-hours call → watch digest → graduate answer_mode. SIP problems: read the
`problems` list from brain `sip-config` first (contract).

## Close the day (sparky app)
`/sparky` → book/reply/approve/log per item → close_case → weekly `/sparky/export`
CSV to accountant. Retention: `python3 -m app.retention` (dry-run; `--apply` deletes).

## Push work (tokens!)
Feature branches only; push with one-shot token URL, never store it; revoke after.
`git push <token-url> <branch>` — see AGENTS.md runbook.
