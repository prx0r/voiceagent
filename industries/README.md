# Industries — index + cross-cutting law

| File | Vertical | Role |
|---|---|---|
| electrical.md | Electrical contractors | Wedge #1: after-hours + EICR engine |
| ev_charging.md | EV chargepoint installs | Acquisition spear: one job type, regulated, stuck customers |
| msp_it.md | MSP / IT support | Wedge #2: bigger ARPU, longer cycles, heavier law |
| plumbing_heating.md | Plumbing & heating | Proof the kernel ports; gas fenced hard |

Market numbers: docs/UK_MARKET.md. Competitors: docs/competitors/. Stack: docs/ARCHITECTURE_SYNTH.md.

## Cross-cutting law (applies to every vertical)
- **UK GDPR + DPA 2018 (+ Data (Use and Access) Act 2025):** minimise PII before
  logging; processor terms per client; retention enforced (app/retention.py); never
  train on conversations. Breach playbook in the MSA.
- **PECR:** consent receipts for all follow-up/review texts; TPS screen marketing
  calls; instigator liability means OUR templates must be compliant even when the
  sparky presses send.
- **Call recording (IPA 2016 + 2018 Business Regs):** "calls recorded" greeting +
  client consent in MSA + retention limits = lawful basis. Already designed in.
- **Consumer Rights Act 2015:** written scope + validity on every quote; case file
  as evidence. Same discipline everywhere.
- **No standalone UK AI law** (principles-based via regulators as of 2026): comply
  via sector law above + documented human-approval thresholds, not AI-specific filings.

## Legislation → product requirement map
| Legal duty | Where it lives in code |
|---|---|
| Inform callers of recording | livekit_agent/prompts.py greeting + /quote page notice |
| Minimise + expire personal data | app/retention.py policies; PII redaction before logging |
| Consent for follow-up texts | funnel booking captures + stores consent; tools/whatsapp.py checks |
| Provable authority for actions | confirm/approval tokens + it_audit.jsonl receipts (CMA 1990 evidence) |
| Refuse dangerous classes | ittools REFUSE + evtools safety escalation (electrical/gas) |
| Recurring compliance demand | EICR/gas-cert reminder flows (roadmap: cron over case store) |
| Never guarantee regulated outcomes | graph policies (grants/DNO/eligibility non-guarantee wording) + guard |
