"""Subgraph connector — attach any graph to the kernel.

The kernel works with a YAML config that defines nodes and edges.
This module makes it easy to:
1. Load a YAML config
2. Attach it to the kernel
3. Swap configs at runtime
4. Merge multiple graphs
"""
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any


def load_graph_config(path: str) -> dict:
    """Load a graph config from YAML."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_configs(base: dict, overlay: dict) -> dict:
    """Merge two graph configs. Overlay takes precedence."""
    result = dict(base)
    
    # Merge nodes
    if "nodes" in overlay:
        base_nodes = {n["id"]: n for n in result.get("nodes", [])}
        for node in overlay["nodes"]:
            base_nodes[node["id"]] = node
        result["nodes"] = list(base_nodes.values())
    
    # Merge edges
    if "edges" in overlay:
        base_edges = result.get("edges", [])
        result["edges"] = base_edges + overlay["edges"]
    
    # Merge business info
    if "business" in overlay:
        result["business"] = {**result.get("business", {}), **overlay["business"]}
    
    return result


def create_graph_from_product_list(products: list[dict]) -> dict:
    """Create a graph config from a product list.
    
    Each product dict should have:
    - id: unique identifier
    - name: product name
    - aliases: alternative names
    - compatibility: list of compatible product IDs
    - price: price info
    """
    nodes = []
    edges = []
    
    for p in products:
        node = {
            "id": p["id"],
            "type": "product",
            "name": p["name"],
            "aliases": p.get("aliases", []),
            "text": p.get("description", ""),
            "metadata": {
                "price": p.get("price", "unknown"),
                "mpn": p.get("mpn", ""),
            }
        }
        nodes.append(node)
        
        for compat_id in p.get("compatibility", []):
            edges.append({
                "source": p["id"],
                "target": compat_id,
                "relation": "compatible_with",
                "weight": 1.0
            })
    
    return {
        "business": {"name": "Product Catalog", "locale": "en"},
        "nodes": nodes,
        "edges": edges,
    }


def create_graph_from_csv(csv_path: str) -> dict:
    """Create a graph from a CSV file with columns: id, name, aliases, compatibility, price."""
    import csv
    
    nodes = []
    edges = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node = {
                "id": row["id"],
                "type": "product",
                "name": row["name"],
                "aliases": row.get("aliases", "").split("|"),
                "text": row.get("description", ""),
                "metadata": {"price": row.get("price", "")}
            }
            nodes.append(node)
            
            for compat in row.get("compatibility", "").split("|"):
                if compat:
                    edges.append({
                        "source": row["id"],
                        "target": compat,
                        "relation": "compatible_with"
                    })
    
    return {"business": {"name": "Imported Catalog", "locale": "en"}, "nodes": nodes, "edges": edges}
