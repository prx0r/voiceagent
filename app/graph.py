from __future__ import annotations
import math, re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)

def toks(s: str) -> set[str]:
    return {x.lower() for x in TOKEN_RE.findall(s or "") if len(x) > 1}

@dataclass
class Hit:
    node_id: str
    score: float
    node: dict[str, Any]
    via: str = "lexical"

class KnowledgeGraph:
    """Tiny dependency-free graph retriever.

    Default MVP strategy:
      1. lexical/entity recall over names, aliases and text
      2. type/metadata boosts
      3. graph-neighbour expansion
      4. evidence is passed to the LLM, never silently treated as fact

    Swap this for Neo4j/GraphRAG later without changing the chat API.
    """
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.nodes = {n["id"]: n for n in config.get("nodes", [])}
        self.edges = config.get("edges", [])
        self.adj = defaultdict(list)
        for e in self.edges:
            self.adj[e["source"]].append((e["target"], e))
            if e.get("bidirectional", True):
                self.adj[e["target"]].append((e["source"], e))
        self.doc_tokens = {}
        self.df = defaultdict(int)
        for nid, node in self.nodes.items():
            text = " ".join([
                node.get("name", ""), node.get("text", ""),
                " ".join(node.get("aliases", [])),
                " ".join(f"{k} {v}" for k,v in node.get("metadata", {}).items()),
            ])
            tt = toks(text)
            self.doc_tokens[nid] = tt
            for t in tt:
                self.df[t] += 1

    def search(self, query: str, top_k: int = 6) -> list[Hit]:
        q = toks(query)
        if not q:
            return []
        N = max(1, len(self.nodes))
        hits: list[Hit] = []
        for nid, dt in self.doc_tokens.items():
            overlap = q & dt
            if not overlap:
                continue
            score = sum(math.log((N + 1)/(self.df[t] + 1)) + 1 for t in overlap)
            node = self.nodes[nid]
            name_alias = toks(node.get("name", "") + " " + " ".join(node.get("aliases", [])))
            score += 2.0 * len(q & name_alias)
            if node.get("type") in {"policy", "faq", "service", "product", "location"}:
                score *= 1.12
            hits.append(Hit(nid, score, node))
        hits.sort(key=lambda h: h.score, reverse=True)
        seeds = hits[:top_k]
        expanded = {h.node_id: h for h in seeds}
        for h in seeds[:3]:
            for neighbour, edge in self.adj.get(h.node_id, []):
                if neighbour not in self.nodes:
                    continue
                boost = h.score * 0.28 * float(edge.get("weight", 1.0))
                old = expanded.get(neighbour)
                if not old or boost > old.score:
                    expanded[neighbour] = Hit(neighbour, boost, self.nodes[neighbour], f"edge:{edge.get('relation','related')}")
        return sorted(expanded.values(), key=lambda h: h.score, reverse=True)[:top_k]

    def context(self, query: str, top_k: int = 6) -> tuple[str, list[dict]]:
        hits = self.search(query, top_k)
        evidence = []
        chunks = []
        for h in hits:
            n = h.node
            chunks.append(f"[{n['id']}] TYPE={n.get('type')} NAME={n.get('name')}\n{n.get('text','')}\nMETA={n.get('metadata',{})}")
            evidence.append({"id": n["id"], "name": n.get("name"), "type": n.get("type"), "score": round(h.score, 3), "via": h.via})
        return "\n\n".join(chunks), evidence
