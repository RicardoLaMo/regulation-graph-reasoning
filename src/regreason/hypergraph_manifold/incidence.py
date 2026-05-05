"""Build the complaint↔regulation hypergraph.

Nodes:
  C_i: complaint nodes (one per row in the answers DataFrame)
  R_j: regulation-section nodes (one per RegSection)

Hyperedges (one per non-empty (Conduct, Route) pair):
  - a complaint joins if its AnswerObject lists that conduct AND maps to that route
  - a reg section joins if its conduct_tags ∩ {conduct} != ∅ AND route_tags ∋ route

Auxiliary hyperedges per Product (membership = product label).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ..io_loaders import RegSection
from ..ontology import ConductType, RouteTarget


@dataclass
class Hypergraph:
    node_ids: List[str]
    node_types: List[str]                  # "complaint" or "regulation"
    incidence: np.ndarray                  # (N, E) {0, 1}
    hyperedge_names: List[str]
    edge_meta: List[Dict] = field(default_factory=list)
    # node-level features
    node_features: np.ndarray = None       # (N, d)
    # secondary attributes
    products: List[str] = field(default_factory=list)
    conducts_per_node: List[List[str]] = field(default_factory=list)


def build_incidence(
    answers: pd.DataFrame,
    regs: List[RegSection],
    complaint_emb: np.ndarray,
    reg_emb: np.ndarray,
    product_col: str = "product",
    conducts_col: str = "conducts",
    route_col: str = "route",
    complaint_id_col: str = "complaint_id",
) -> Hypergraph:
    n_c = len(answers)
    n_r = len(regs)

    node_ids: List[str] = []
    node_types: List[str] = []
    products: List[str] = []
    conducts_per_node: List[List[str]] = []

    for _, row in answers.iterrows():
        node_ids.append(f"C:{row[complaint_id_col]}")
        node_types.append("complaint")
        products.append(str(row[product_col]))
        cs = row[conducts_col]
        if isinstance(cs, str):
            cs = [cs] if cs else []
        elif cs is None:
            cs = []
        conducts_per_node.append(list(cs))

    for r in regs:
        node_ids.append(f"R:{r.section_id}")
        node_types.append("regulation")
        products.append(r.regulation)
        conducts_per_node.append(list(r.conduct_tags))

    edge_keys: List[Tuple[str, str]] = []
    for c in ConductType:
        for rt in RouteTarget:
            edge_keys.append((c.value, rt.value))

    cols: List[np.ndarray] = []
    edge_names: List[str] = []
    edge_meta: List[Dict] = []

    routes_complaints = answers[route_col].astype(str).tolist()

    for cval, rval in edge_keys:
        col = np.zeros(n_c + n_r, dtype=np.int8)
        # complaints: (cval in conducts) AND (route == rval)
        for i, (cs, rt) in enumerate(zip(conducts_per_node[:n_c], routes_complaints)):
            if cval in cs and rt == rval:
                col[i] = 1
        # regulations: (cval in conduct_tags) AND (rval in route_tags)
        for j, r in enumerate(regs):
            if cval in r.conduct_tags and rval in r.route_tags:
                col[n_c + j] = 1
        if col.sum() == 0:
            continue
        cols.append(col)
        edge_names.append(f"E_{cval}__{rval}")
        edge_meta.append({"conduct": cval, "route": rval, "n_members": int(col.sum())})

    # Auxiliary product hyperedges (membership only across complaint nodes; few regs declare a product)
    for prod in sorted(set(products[:n_c])):
        col = np.zeros(n_c + n_r, dtype=np.int8)
        for i in range(n_c):
            if products[i] == prod:
                col[i] = 1
        if col.sum() == 0:
            continue
        cols.append(col)
        edge_names.append(f"P_{prod[:24]}")
        edge_meta.append({"product": prod, "kind": "auxiliary", "n_members": int(col.sum())})

    if cols:
        H = np.stack(cols, axis=1)
    else:
        H = np.zeros((n_c + n_r, 0), dtype=np.int8)

    node_features = np.vstack([complaint_emb, reg_emb]).astype("float32")

    return Hypergraph(
        node_ids=node_ids,
        node_types=node_types,
        incidence=H,
        hyperedge_names=edge_names,
        edge_meta=edge_meta,
        node_features=node_features,
        products=products,
        conducts_per_node=conducts_per_node,
    )


def clique_expand_edges(H: np.ndarray, max_members_per_edge: int = 30,
                        seed: int = 42) -> np.ndarray:
    """Convert incidence H (N, E) to a list of (src, dst) pairs (clique expansion).

    To keep memory bounded, when a hyperedge has more than ``max_members_per_edge``
    members we randomly subsample (deterministic via ``seed``) before forming
    the clique. With 5,000 complaints and ~50 hyperedges, full clique expansion
    would produce O(N^2) edges per hyperedge. Capping at 30 keeps the GAT
    forward pass under a few GB of GPU memory and preserves the manifold
    structure (each member connects to ~30 same-edge peers, more than enough
    for two GAT layers).
    """
    rng = np.random.default_rng(seed)
    N, E = H.shape
    pairs = []
    for e in range(E):
        members = np.where(H[:, e] > 0)[0]
        if len(members) < 2:
            continue
        if len(members) > max_members_per_edge:
            members = rng.choice(members, size=max_members_per_edge, replace=False)
        for i in range(len(members)):
            for j in range(len(members)):
                if i == j:
                    continue
                pairs.append((int(members[i]), int(members[j])))
    if not pairs:
        return np.zeros((2, 0), dtype=np.int64)
    arr = np.array(pairs, dtype=np.int64).T
    return arr
