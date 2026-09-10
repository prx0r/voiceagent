# Call-transcript datasets (2026-09-10)

## Downloaded (sampled, in repo)
- `data/call_transcripts/home_service_sample.json` (41KB, 40 calls, caller turns only)
  Curated by `scripts/curate_transcripts.py` from:
- **yevgeniy03/home-telecom-callcenter-transcripts-viewer** (HF): flattened viewer of
  one AIxBlock 92k zip — 3,239 home/telecom transcripts as Parquet (20MB, /tmp only,
  NOT committed). PII-redacted, word timestamps, turn-split (Agent/Customer/IVR).
  License: check repo card before commercial training use; our use = triage/retrieval
  characterization only.

## Characterized (scripts/eval_transcripts.py)
40 real home-service caller texts @11pm → 40 routine, 0 wake (correct: property
restoration claims, none electrical). Drove two triage fixes: arcing-signal coverage,
negation guard, word-boundary matching ("hot"⊂"shot"/"photos").

## Full corpus (not downloaded — GBs, needs justification)
- **AIxBlock/92k-real-world-call-center-scripts-english** (HF): 91,706 transcripts,
  ~10,500 hrs, domain/topic/accent tags, PII-redacted + paper (arXiv 2507.02958).
  Pull domain-filtered slices only when a drill needs them.
- AxonData english-contact-center-audio (1,000+ hrs, commercial-gated): skip unless
  training STT.
- google-research-datasets/schema_guided_dstc8 (18k task dialogues, services/APIs):
  useful for tool-call/intent benchmarking, not sparky content.
- Abhinav242004/multi_woz_v22 (Apache 2.0): booking-flow patterns only.

## Rules
Raw corpora stay out of git (size + license hygiene). Committed samples only, small,
redacted, with source + script that produced them.
