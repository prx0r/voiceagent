#!/usr/bin/env python3
"""Batch-characterize real caller transcripts through our kernel (report, not test).

Reads data/call_transcripts/home_service_sample.json (curated, committed),
runs each caller text through triage_urgency + EV graph retrieval, prints the
distribution. Use to spot triage/retrieval drift after kernel changes.
Run: python3 scripts/eval_transcripts.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    import yaml
    from app import evtools
    from app.graph import KnowledgeGraph
    sample = json.loads(Path("data/call_transcripts/home_service_sample.json").read_text())["calls"]
    cfg = yaml.safe_load(open("knowledge/ev_charger_install_en.yaml"))
    g = KnowledgeGraph(cfg)
    levels, tops, wakes = Counter(), Counter(), []
    for c in sample:
        t = evtools.triage_urgency(c["caller_text"], hour=23)
        levels[t["level"]] += 1
        hits = g.search(c["caller_text"], 3)
        top = hits[0].node_id if hits else "none"
        tops[top] += 1
        if t["level"] == "wake_now":
            wakes.append((c["transcript_id"], c["caller_text"][:100]))
    print(f"{len(sample)} real caller texts (home-service, 11pm):")
    print("triage:", dict(levels))
    print("top evidence:", dict(tops.most_common(8)))
    print(f"would-wake ({len(wakes)}):")
    for tid, preview in wakes[:10]:
        print(f"  {tid}: {preview}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
