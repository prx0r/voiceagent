# Shared kernel schema v0.1 (DRAFT for brain box — Phase 0 joint artifact)

One biz file, both test suites load it. Superset of voice tradie_profile.yaml and
brain knowledge/<biz>_en.yaml: voice reads business/agent/voice/nodes (+ evidence),
brain reads tradie block (prices, prefs, multipliers); each ignores the other's block.

```yaml
business: {name, locale, phone, hours{}}
agent: {system_prompt}            # voice wording constraints (ranges, non-guarantees)
voice: {edge_voice, production_note}
tradie: {name, business, base_postcode, phone, scheme, calendar{file, slot_min, buffer_min}}
preferences: {mornings_first, workdays[], saturday_ok, max_drive_min, enjoys[], dislikes[]}
prices: {callout_weekday, callout_saturday, hourly, ev_7kw_standard[lo,hi], ...}  # RANGES ONLY
quotes: {flexibility, validity_days, deposit}
messages: {tone, signoff, on_my_way}
nodes:                                    # graph evidence (voice reads, brain serves)
  - {id, type, name, aliases[], text}
edges:
  - {source, target, relation}            # governed_by | requires | try_first | can_trigger
```

Conformance (both sides assert): required top-level keys present; every prices value
is a range or labeled estimate (no bare final numbers); every node has id+text; every
edge endpoint exists; safety node present with wake aliases; policy nodes carry
non-guarantee wording (grants/DNO/eligibility). Versioned: `kernel_version: 0.1`.
