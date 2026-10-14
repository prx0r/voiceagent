#!/usr/bin/env python3
"""Generate per-prospect demo sites: CSV row -> slug.aionboard.co.uk folder.

Usage:
  python3 scripts/generate_demos.py --csv ../aionboard/prospects_manchester_top50.csv --trade electrician --limit 5
  # out/sites/<slug>/index.html (BUSINESS, logo letter, trade content via /api/industries)

Trade comes from --trade (slug in app.industries TRADES). Serve out/ on any
domain with wildcard DNS (*.aionboard.co.uk) + a static host; the page calls
back to /api/* on the same host.
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.industries import TRADES  # noqa: E402


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    s = re.sub(r"-(ltd|limited|plc|co|services|electrical|electric)\b", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-") or "prospect"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--trade", required=True)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="sites")
    args = ap.parse_args()
    trade = next((t for t in TRADES if t["slug"] == args.trade), None)
    if not trade:
        print(f"unknown trade (pick: {[t['slug'] for t in TRADES]})")
        return 1
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "static", "demo_template.html")).read()
    made = []
    with open(args.csv, newline="", encoding="utf-8", errors="replace") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= args.limit:
                break
            name = (row.get("name") or "Your Business").strip().title()
            area = (row.get("region") or row.get("postcode") or "").strip()
            slug = slugify(row.get("name") or f"prospect-{i}")
            html = tpl.replace("{{BUSINESS}}", name)\
                      .replace("{{TRADE_LABEL}}", trade["label"])\
                      .replace("{{TRADE}}", trade["slug"])\
                      .replace("{{ICON}}", trade["icon"])\
                      .replace("{{TAGLINE}}", trade["tagline"])\
                      .replace("{{AREA}}", area)\
                      .replace("{{SLUG}}", slug)
            d = os.path.join(args.out, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "index.html"), "w").write(html)
            made.append(slug)
    print(f"made {len(made)}: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
