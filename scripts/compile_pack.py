#!/usr/bin/env python3
"""Compile a business YAML into support.pack.v1. Usage:
  python3 scripts/compile_pack.py knowledge/generic_service_business.yaml
Validates references, then writes <stem>.support/manifest.json. Exit 1 on error.
"""
import hashlib
import json
import sys
from pathlib import Path

import yaml


def compile_pack(path: str) -> dict:
    cfg = yaml.safe_load(open(path))
    errors = []
    b = cfg.get("business", {})
    if not b.get("name"):
        errors.append("business.name required")
    if not (cfg.get("agent", {}).get("system_prompt") or "").strip():
        errors.append("agent.system_prompt required")
    ids = set()
    for n in cfg.get("nodes", []) or []:
        if not n.get("id") or not n.get("type") or not n.get("text"):
            errors.append(f"node missing id/type/text: {n.get('id', '?')}")
        ids.add(n.get("id"))
    if not any((n.get("type") == "escalation") for n in cfg.get("nodes", []) or []):
        errors.append("at least one escalation node required")
    for e in cfg.get("edges", []) or []:
        for end in ("source", "target"):
            if e.get(end) not in ids:
                errors.append(f"edge {end} unknown: {e.get(end)}")
    if errors:
        return {"ok": False, "errors": errors}
    canon = json.dumps(cfg, sort_keys=True)
    manifest = {
        "schema": "support.pack/v1",
        "name": b.get("name"),
        "pack_id": "pack_" + hashlib.sha256(canon.encode()).hexdigest()[:12],
        "nodes": len(cfg.get("nodes", [])),
        "edges": len(cfg.get("edges", [])),
        "source": Path(path).name,
    }
    out = Path(path).parent / (Path(path).stem + ".support")
    out.mkdir(exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    manifest["ok"] = True
    manifest["pack"] = str(out)
    return manifest


if __name__ == "__main__":
    r = compile_pack(sys.argv[1])
    print(json.dumps(r, indent=1))
    raise SystemExit(0 if r.get("ok") else 1)
