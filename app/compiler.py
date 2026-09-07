"""Graph compiler — converts subgraph to voice/chat/resolver formats.

One verified graph → every commerce surface.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def compile_to_voice(graph: dict, language: str = "en") -> dict:
    """Compile graph to voiceagent YAML config."""
    nodes = []
    edges = []
    
    entities = graph.get("entities", [])
    if isinstance(entities, list):
        for entity in entities:
            node = {
                "id": entity.get("id", ""),
                "type": entity.get("type", "product"),
                "name": entity.get("name", ""),
                "aliases": entity.get("aliases", []),
                "text": entity.get("description", ""),
            }
            if entity.get("metadata"):
                node["metadata"] = entity["metadata"]
            nodes.append(node)
    
    for edge in graph.get("edges", []):
        edges.append({
            "source": edge["from"],
            "target": edge["to"],
            "relation": edge["relation"],
            "weight": edge.get("weight", 1.0),
        })
    
    return {
        "business": {"name": graph.get("name", ""), "locale": language},
        "nodes": nodes,
        "edges": edges,
    }


def compile_to_questions(graph: dict) -> list:
    """Compile graph to disambiguation questions for Google Merchant Center."""
    questions = []
    
    for q in graph.get("questions", []):
        questions.append({
            "question": q["question"],
            "answer": q["answer"],
        })
    
    return questions


def compile_to_product_detail(graph: dict) -> list:
    """Compile graph to Google Merchant Center product_detail attributes."""
    details = []
    
    for entity_id, entity in graph.get("entities", {}).items():
        if entity.get("type") == "PART":
            for key, value in entity.items():
                if key not in ("id", "name", "type"):
                    details.append({
                        "attribute_name": f"Compatibility:{key}",
                        "attribute_value": str(value),
                    })
    
    return details


def compile_to_resolver(graph: dict) -> dict:
    """Compile graph to resolver API format."""
    entities = graph.get("entities", {})
    edges = graph.get("edges", [])
    
    # Build adjacency list
    adj = defaultdict(list)
    for edge in edges:
        adj[edge["from"]].append({
            "target": edge["to"],
            "relation": edge["relation"],
            "qualifiers": edge.get("qualifiers", {}),
        })
    
    return {
        "entities": entities,
        "adjacency": dict(adj),
        "resolver_endpoints": [
            {"name": "identify", "description": "Identify a part from photo/markings"},
            {"name": "resolve", "description": "Resolve compatibility for a component"},
            {"name": "substitute", "description": "Find replacement parts"},
            {"name": "check_stock", "description": "Check supplier stock"},
            {"name": "get_price", "description": "Get price from supplier"},
        ],
    }


def compile_all(graph: dict, output_dir: str):
    """Compile graph to all formats."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    # Voice config
    voice_config = compile_to_voice(graph, "en")
    (out / "voiceagent.yaml").write_text(json.dumps(voice_config, indent=2))
    
    # Questions
    questions = compile_to_questions(graph)
    (out / "questions.json").write_text(json.dumps(questions, indent=2))
    
    # Product details
    details = compile_to_product_detail(graph)
    (out / "product_detail.json").write_text(json.dumps(details, indent=2))
    
    # Resolver
    resolver = compile_to_resolver(graph)
    (out / "resolver.json").write_text(json.dumps(resolver, indent=2))
    
    # Raw graph
    (out / "graph.json").write_text(json.dumps(graph, indent=2))
    
    print(f"Compiled to {out}:")
    for f in out.iterdir():
        print(f"  {f.name}: {f.stat().st_size/1000:.1f}KB")
