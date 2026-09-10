# PROJECT_STANDARD — starter kernel for autonomous codebases

Every repo an agent builds for us MUST ship this shape, so the end result is
beautiful working infra with docs, run/test instructions, and evidence. Enforced
by the repo's own AGENTS.md (copy the laws block, adapt the paths).

## Required layout
```
AGENTS.md            # absolute laws + where-things-are + runbook (binding)
NORTHSTAR.md         # vision + lane boundaries (what this repo does NOT do)
README.md            # 60-second start (install → run → verify)
.env.example         # EVERY env var with safe defaults (fresh clone must boot)
docs/README.md       # index: read-this-when table
docs/RECIPES.md      # copy-paste operations (no prose-only procedures)
docs/FILES.md        # one line per file + status (audit, updated per feature)
docs/MCP.md          # future agent surface (planned tools table, even if unbuilt)
docs/THREADS.md      # open threads with owners (nothing lives only in chat)
tests/               # mirrors source; regression test per fix; suite green = shippable
scripts/             # runnable scenarios/e2e (exit codes honest: 0 green, 1 red)
evidence/ or var/    # timestamped run logs (digest-pinned where security-relevant)
```

## Laws template (adapt brackets)
1. [Authority rule: what is ground truth here, what may never invent it]
2. [Side-effect rule: approvals/tokens required; refusal classes named]
3. [State rule: where state lives; conversation/logs are not state]
4. [Degradation rule: what works offline/without keys; sync-back behavior]
5. [Honesty rule: mocks prove wiring never quality; simulated numbers labeled;
   no live claims without a live run; exit codes never masked by pipes]
6. [License rule: AGPL patterns-only never pasted; MIT/Apache vendored w/ attribution]
7. [Secret rule: redaction tiers; .env never committed; tokens one-shot + revoked]

## Runbook template (every README + AGENTS.md)
install → configure (.env) → run → verify (tests + scenario scripts with expected
counts, e.g. "expect 8/8") → operate (retention/backup) → push (branch policy).
Fresh-clone-to-green must work with zero tribal knowledge.

## Done-definition (per feature)
Code + test proving its honesty property + recipe entry + FILES.md line +
THREADS.md update + evidence log where security-relevant. A feature without all
five is not done.
