#!/usr/bin/env python3
"""Curate a small caller-side sample from the downloaded home-service corpus.

Source: yevgeniy03/home-telecom-callcenter-transcripts-viewer (viewer copy of
AIxBlock 92k real-world call-center transcripts, PII-redacted). Input parquet
lives OUTSIDE the repo (/tmp/opencode/calldata — 20MB, not committed).
Output: data/call_transcripts/home_service_sample.json (~40 calls, caller turns
only, truncated) — small enough to commit and run in CI.
"""
import json
import re
import sys
from pathlib import Path

SRC = Path("/tmp/opencode/calldata/data/train.parquet")
OUT = Path(__file__).resolve().parent.parent / "data" / "call_transcripts" / "home_service_sample.json"
N = 40
TURN_RE = re.compile(r"\[[^\]]+\] (Customer|Agent|IVR/System|Unknown): (.*?)(?=\n\[[^\]]+\] |\Z)", re.S)


def caller_text(dialogue: str, max_chars: int = 900) -> str:
    parts = [m.group(2).strip() for m in TURN_RE.finditer(dialogue or "")
             if m.group(1) == "Customer"]
    text = " ".join(parts)
    text = re.sub(r"\[(ORGANIZATION|PERSON_NAME|OCCUPATION|PHONE|ADDRESS)[^\]]*\]", "[REDACTED]", text)
    return text[:max_chars].strip()


def main() -> int:
    import pyarrow.parquet as pq
    rows = pq.read_table(SRC).to_pylist()
    hs = [r for r in rows if r.get("filename_domain_hint") == "home_service"
          and not r.get("is_empty_text")]
    # Prefer meatier calls with real back-and-forth
    hs.sort(key=lambda r: r.get("customer_turn_count", 0) or 0, reverse=True)
    sample = []
    for r in hs[:N]:
        ct = caller_text(r.get("dialogue_text_inferred", ""))
        if len(ct) < 120:
            continue
        sample.append({"transcript_id": r["transcript_id"],
                       "caller_text": ct,
                       "customer_turns": r.get("customer_turn_count", 0),
                       "word_count": r.get("word_count", 0)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "yevgeniy03/home-telecom-callcenter-transcripts-viewer (AIxBlock 92k, PII-redacted)",
                               "calls": sample}, indent=1))
    print(f"wrote {len(sample)} calls -> {OUT} ({OUT.stat().st_size/1024:.0f}KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
