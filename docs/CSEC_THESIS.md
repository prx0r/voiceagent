# CSEC thesis — aisec applied to our own stack (2026-09-10)

## One line
As agents run businesses, every customer-facing surface becomes an extraction
surface. We ship the agent stack (cmail + voiceagent) AND the red team that proves
it holds. Dogfood first, product second: csec attacks our stack, then sells the
corpus + continuous testing to everyone else running agents.

## Why us, why now
- The threat model already exists both sides: cmail `THREATMODEL.md` (money, client
  list, intel, identity, attention — 7 vectors, tiered controls) and aisec Lab 1/2
  (agent control + AI-enabled adversary simulation). csec is the loop that joins them.
- aisec `worlds/voiceagent/` already holds attack-run evidence vs a voice target —
  the harness pattern exists; point it at OUR endpoints.
- Every control we sell is one we run: confirm-tokens (CMA 1990 evidence), guard +
  quarantine, drafts-only sends, audit logs, retention sweeps. Attackers test the
  demo, customers buy the controls.

## Attack surface map (stack-wide)
| Surface | Entry | Extraction target | csec test pack |
|---|---|---|---|
| Voice calls | spoken injection, social engineering across turns | quotes/prices, wake-now abuse, callback fraud | jailbreak + authority-claim + urgency-spoof call scripts; guard-trip assertions |
| Email bus | direct/indirect injection, forwarded threads, attachments | exfil via summaries, fake approvals | injection-quarantine probes; tool-output exfil attempts |
| WhatsApp/IG DMs | display-name spoofing, rapport-then-escalate | client list, send-as identity | sender-tier bypass attempts; send-as-scam drills |
| Job/quote/invoice flow | fake refund/approval, margin pumping | money, intel (price book) | approval-token replay/theft; competitor intel-pump sessions |
| Kernel/config | rogue skill edit widening autonomy | whole business (silent) | autonomy-diff monitoring; price-book exfil attempts |
| Human queue | approval fatigue floods | rubber-stamp payout | flood simulations; wake-now rate-limit verification |

## Product loop (mirrors aisec growth loop, scoped to our stack)
```
new attack/research → reproduce vs OUR endpoints → regression test in repo
→ control ships both boxes → sanitized writeup → free voiceagent audit offer
→ paid csec engagement → continuous testing retainer ("does the new trick
work against YOUR sparky?")
```

## Business shape
- Free: voiceagent security self-check (attack scripts vs your own deployment).
- Paid: targeted simulation (£500-2k), full adversarial assessment (£2k-10k),
  continuous testing retainer (monthly new-attack sweep) — same ladder as aisec.
- Differentiator vs generic pentest: industry-shaped attacks (sparky emergency
  spoofing, EICR intel pumping, supplier impersonation) + the fix lands as code
  in the stack, retested, not a PDF.
- x402 angle (aisec IDEAS.md): pay-per-request red-team endpoint on prx0r/x402 —
  agents buying security tests for themselves, machine-to-machine.

## Non-overlap rules (avoid three-way confusion)
- aisec = research lab + corpus + methodology (upstream, industry-wide).
- csec = productized practice ON our stack (voiceagent + cmail deployments).
- cmail/voiceagent = the systems under test AND the fix delivery vehicle.
Evidence flows up (csec runs → aisec corpus); controls flow down (aisec research →
csec packs → stack code).
