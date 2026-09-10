# MSP / IT support (UK) — industry report

Snapshot: £50bn+ spend, 11,500+ MSPs; L1 >20% of cost (~£6.50 true cost/ticket);
outsourced NOC £4-6k/mo; 8x5→24x7 adds 30-50%. See UK_MARKET.md. Our edge vs Struan/
DaemonLayer: voice calls + gated action engine. Higher ARPU, longer cycles, heavier
compliance — second wedge after trades.

## Legislation that shapes the product (the "legal shit", itemised)

| Law / instrument | Requirement | Product implication |
|---|---|---|
| UK GDPR + Data Protection Act 2018 (+ Data (Use and Access) Act 2025, in force 19 Jun 2025) | Lawful basis, data minimisation, Art 28 processor terms, breach notification (ICO 72h controller duty), rights handling | Per-client DPA; PII minimisation before logging; retention sweeper with teeth; no training on client conversations (also a WhatsApp ToS ban). |
| Computer Misuse Act 1990 s.1 | Offence to cause a computer to perform functions to secure unauthorised access | THE action-agent law: every action needs provable authority (client contract + per-action confirm token). Our confirm-token receipts ARE the authorisation evidence. No token, no action, no exceptions. |
| Investigatory Powers Act 2016 s.3 + Interception by Businesses Regs 2018 (regs 3-4) | Interception offence without lawful authority; business monitoring/recording allowed for legitimate purposes with system-controller consent + reasonable efforts to inform users | Call-recording/monitoring lawful basis: record for QA/compliance + inform every caller ("calls recorded" greeting) + system-controller (client) consent in MSA. Already in our greeting + retention design. |
| Privacy and Electronic Communications Regs 2003 (PECR) | Opt-in consent for unsolicited marketing calls/texts/emails; live vs automated call rules; TPS screening; B2B vs sole-trader distinctions; instigator liability (you're liable even if a contractor sends) | Outreach/follow-up flows need consent records + TPS checks; review-request texts need consent basis. Our funnel captures consent at booking — keep the receipt. |
| Network and Information Systems Regulations 2018 | Duties on operators of essential services + relevant digital service providers (security measures, incident notification) | For in-scope clients: agent actions constrained to approved runbooks; incident-escalation path documented; never auto-remediate security incidents. |
| Product Security and Telecommunications Infrastructure Act 2022 | Security baselines for connectable products (no default passwords etc.) | When handling smart/IoT devices: never set weak defaults; credential handling stays refused-class. |
| Cyber Essentials / Plus (NCSC) + client frameworks (FCA resilience, ISO 27001) | Baseline controls often contractual; evidence on demand | Audit exports (it_audit.jsonl per action) double as compliance evidence; first-time-fix + SLA dashboards feed QBRs. |
| Consumer Rights Act 2015 / B2B contract law | Service standards; liability caps live in the MSA | MSA must name the no-go list (mirrors our refusal classes), liability caps, and human-approval thresholds. The tiers are the legal architecture — sell them as such. |

## No-go list (refused by default, human only)
Deletes/data destruction, firewall/security changes, credential/password handling,
bulk comms without consent proof, auto-remediation of live security incidents.
Anything here goes ticket + human + written approval. This list belongs in every MSA.
