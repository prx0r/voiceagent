# HANDOVER — Next Agent

## State of Play

### Voice Agent (`/root/voiceagent/`)
- 3 configs: Norwegian (balcony doors), English (hot-tub panels), Finnish (hot-tub panels)
- Graph: 20 nodes per config, TF-IDF search
- Test scores: Norwegian 9/10, Finnish 8/10, English 7/10
- TTS: Edge TTS working for all 3 languages
- Pushed to: github.com/prx0r/voiceagent

### BitSec (`/root/bitt/`)
- Auditor: 17/22 (73%) with 22 guidance entries
- Agent: 16/22 in sandbox format
- Proxy: fixed (x-opencode-session header)
- Main issue: non-determinism (30-70% variance)

### Drop (`/root/dropcomp/`)
- 6 niches mapped, 30+ competitors
- Structured JSON schemas
- Pushed to: github.com/prx0r/dropcomp

## What the User Wants Next

1. Port voice agent to Finnish — DONE
2. Create build notes — DONE
3. Prepare handover — THIS

## Architecture (from user's analysis)

The real product is:
> **one verified compatibility graph that compiles losslessly into every human and agent commerce surface.**

Not a store. Not a voice agent. A graph compiler.

## Next Steps for Next Agent

1. Demote 25 campaigns to truthful states
2. Define subgraph.schema.v1
3. Build first evidence-backed real subgraph (balcony-door hardware)
4. Modify voiceagent to load compiled Drop graphs
5. Build Shopify Admin/metafield compiler
6. Test live Shopify /api/ucp/mcp endpoint

## Key Files

| File | Purpose |
|------|---------|
| voiceagent/app/graph.py | Knowledge graph engine |
| voiceagent/app/language.py | Language detection |
| voiceagent/app/flow.py | Customer service flow |
| voiceagent/knowledge/*.yaml | Business configs |
| bitt/mining/sn60/candidates/contrastive-v1/evo_auditor.py | BitSec auditor |
| bitt/mining/sn60/candidates/contrastive-v1/evo_loop.py | Evolution loop |
| dropcomp/data/campaigns.json | Campaign schemas |
| dropcomp/data/competitors.json | Competitor data |

## Blockers

1. No OpenRouter key in vault (for BitSec submission)
2. Proxy was broken (fixed: x-opencode-session)
3. Voice agent graph too small (20 nodes, needs 50+)
4. Language detection fails on some sentences
