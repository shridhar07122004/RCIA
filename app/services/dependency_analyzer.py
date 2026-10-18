from __future__ import annotations

import re
from dataclasses import dataclass, asdict

import networkx as nx

from app.services.text_preprocessor import keywords


@dataclass
class DependencyEdge:
    source: str
    target: str
    relationship: str
    evidence: str
    strength: float
    explicit: bool


def build_dependency_graph(requirements) -> tuple[nx.DiGraph, list[DependencyEdge]]:
    graph = nx.DiGraph()
    by_code = {item.code: item for item in requirements}
    for item in requirements:
        graph.add_node(item.code, module=item.module)
    edges: list[DependencyEdge] = []
    for item in requirements:
        for reference in item.references:
            if reference in by_code:
                edge = DependencyEdge(item.code, reference, "explicit reference", f"{item.code} mentions {reference}", 1.0, True)
                graph.add_edge(edge.source, edge.target, **asdict(edge))
                edges.append(edge)
    # Only infer a small number of defensible same-module relationships, avoiding a complete graph.
    for index, left in enumerate(requirements):
        for right in requirements[index + 1:]:
            if left.module == "General" or left.module != right.module:
                continue
            overlap = keywords(left.description) & keywords(right.description)
            if len(overlap) >= 2:
                edge = DependencyEdge(left.code, right.code, "shared module", f"Both requirements address {left.module.lower()} ({', '.join(sorted(overlap)[:4])})", 0.55, False)
                if not graph.has_edge(left.code, right.code):
                    graph.add_edge(left.code, right.code, **asdict(edge))
                    edges.append(edge)
    return graph, edges


def related_strength(graph: nx.DiGraph, source: str, target: str) -> tuple[float, str | None]:
    if graph.has_edge(source, target):
        data = graph.edges[source, target]
        return float(data.get("strength", 0)), data.get("evidence")
    try:
        if nx.has_path(graph, source, target):
            path = nx.shortest_path(graph, source, target)
            strength = max(0.3, 0.7 ** (len(path) - 1))
            return strength, f"Dependency path: {' → '.join(path)}"
    except nx.NetworkXError:
        pass
    return 0.0, None
