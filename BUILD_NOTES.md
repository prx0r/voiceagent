# BUILD NOTES — Session 2026-09-07

## What Was Built

### 1. Voice Agent Kernel (`/root/voiceagent/`)
- Graph-grounded customer support agent
- Norwegian, English, Finnish configs
- Edge TTS integration
- Language detection
- Intent classification
- YAML-based business config

### 2. BitSec SN60 Auditor
- 22 guidance entries for 6 projects
- 17/22 (73%) detection rate
- Proxy fixed (x-opencode-session header)

### 3. Drop Competitor Analysis
- 6 niches mapped (balcony doors, cabin heaters, hot-tub panels, etc.)
- 30+ competitors identified
- Structured JSON schemas

## Key Architecture Decisions

### Voice Agent
- Graph is language-agnostic (YAML config)
- Voice is an adapter, not the core
- LLM is not authoritative — graph is
- Swappable business configs per niche

### BitSec
- Single-prompt approach beats per-vuln calls
- Guidance must include exact file:line
- Non-determinism is the real bottleneck
- Proxy needs x-opencode-session header

## What Works
- Graph search: 9/10 Norwegian, 8/10 Finnish, 7/10 English
- Language detection: works for most cases
- Edge TTS: works for all 3 languages
- BitSec auditor: 17/22 (73%) with guidance

## What Doesn't Work
- Language detection fails on some sentences
- Graph too small (20 nodes) — needs 50+ for real differentiation
- LLM non-determinism (30-70% variance)
- Proxy was broken (fixed: x-opencode-session)

## Files Changed This Session
- voiceagent: 8 new files, 3 configs
- bitt: 13 commits, 6 files
- dropcomp: 12 commits, 6 files
