"""Structural Causal Model: DAG over (Product, Issue, Conduct, Harm, Severity, EvidenceGroundedness, Route, ModelConfidence)."""
from __future__ import annotations

from typing import List, Tuple

import networkx as nx


VARIABLES = [
    "Product",
    "Issue",
    "Conduct",
    "Harm",
    "Severity",
    "EvidenceGroundedness",
    "Route",
    "ModelConfidence",
]

EDGES: List[Tuple[str, str]] = [
    ("Product", "Issue"),
    ("Product", "Conduct"),
    ("Issue", "Conduct"),
    ("Conduct", "Harm"),
    ("Conduct", "Severity"),
    ("Harm", "Severity"),
    ("Conduct", "Route"),
    ("Severity", "Route"),
    ("EvidenceGroundedness", "Route"),
    ("EvidenceGroundedness", "ModelConfidence"),
    ("Route", "ModelConfidence"),
]


def build_dag() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from(VARIABLES)
    g.add_edges_from(EDGES)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError("DAG construction produced a cycle")
    return g


def assumptions_str() -> str:
    return (
        "1) Unconfoundedness given (Product, Issue, Conduct): no hidden cause "
        "jointly affects EvidenceGroundedness and Route once these are conditioned on.\n"
        "2) No hidden mediator between Conduct and Route beyond Severity and "
        "EvidenceGroundedness.\n"
        "3) SUTVA: one complaint's routing does not influence another's.\n"
        "4) Faithfulness: observed conditional independencies in the calibration "
        "set imply absent edges in the DAG.\n"
        "5) Positivity: every (Product, Conduct) cell has both high- and "
        "low-grounding samples; cells failing positivity are excluded with "
        "documentation."
    )


def to_graphml(g: nx.DiGraph, path) -> None:
    nx.write_graphml(g, path)


def to_dot(g: nx.DiGraph) -> str:
    lines = ["digraph SCM {", '  rankdir=LR; node [shape=ellipse, fontsize=10];']
    for n in g.nodes:
        lines.append(f'  {n};')
    for u, v in g.edges:
        lines.append(f'  {u} -> {v};')
    lines.append("}")
    return "\n".join(lines)
