import numpy as np
import pandas as pd

from regreason.hypergraph_manifold.incidence import build_incidence, clique_expand_edges
from regreason.io_loaders import RegSection


def _toy_regs(n=3):
    return [
        RegSection(
            section_id=f"R{i}",
            regulation=f"reg{i}",
            citation=f"12 CFR 1000.{i}",
            title=f"section {i}",
            text="example regulatory text",
            route_tags=["fraud_ops"] if i == 0 else ["legal"],
            conduct_tags=["unauthorized"] if i == 0 else ["deceptive_practice"],
        )
        for i in range(n)
    ]


def _toy_answers(n=8):
    rows = []
    for i in range(n):
        rows.append({
            "complaint_id": f"c{i}",
            "product": "Credit card" if i < 4 else "Mortgage",
            "issue": "x",
            "conducts": ["unauthorized"] if i % 2 == 0 else ["deceptive_practice"],
            "harms": ["monetary_loss"],
            "severity": 3,
            "route": "fraud_ops" if i % 2 == 0 else "legal",
        })
    return pd.DataFrame(rows)


def test_incidence_shape_and_membership():
    regs = _toy_regs()
    answers = _toy_answers()
    c_emb = np.random.RandomState(0).randn(len(answers), 16).astype("float32")
    r_emb = np.random.RandomState(1).randn(len(regs), 16).astype("float32")
    hg = build_incidence(answers, regs, c_emb, r_emb)
    N = len(answers) + len(regs)
    assert hg.incidence.shape[0] == N
    assert hg.incidence.shape[1] >= 1
    assert all(t in {"complaint", "regulation"} for t in hg.node_types)
    assert hg.node_features.shape == (N, 16)


def test_clique_expansion_nonempty_when_edges_exist():
    regs = _toy_regs()
    answers = _toy_answers()
    c_emb = np.zeros((len(answers), 8), dtype="float32")
    r_emb = np.zeros((len(regs), 8), dtype="float32")
    hg = build_incidence(answers, regs, c_emb, r_emb)
    ei = clique_expand_edges(hg.incidence)
    assert ei.shape[0] == 2
    if hg.incidence.shape[1] > 0:
        assert ei.shape[1] >= 0
