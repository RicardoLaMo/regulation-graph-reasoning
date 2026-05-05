import networkx as nx
import numpy as np
import pandas as pd

from regreason.causal.dag import build_dag, assumptions_str, to_dot
from regreason.causal.estimands import do_intervention


def test_dag_is_acyclic():
    g = build_dag()
    assert nx.is_directed_acyclic_graph(g)
    assert "Route" in g.nodes
    assert ("EvidenceGroundedness", "Route") in g.edges


def test_assumptions_nonempty():
    s = assumptions_str()
    assert len(s) > 200
    assert "Unconfoundedness" in s


def test_to_dot_renders():
    s = to_dot(build_dag())
    assert "digraph" in s
    assert "Route" in s


def test_do_intervention_recovers_strong_effect():
    rng = np.random.default_rng(0)
    n = 800
    strata = rng.choice(["s1", "s2"], size=n)
    treat = rng.integers(0, 2, size=n)
    # outcome strongly depends on treatment
    out = treat + 0.1 * rng.standard_normal(n)
    df = pd.DataFrame({"treatment": treat, "outcome": out, "stratum": strata})
    est = do_intervention("test", df, treatment="treatment", outcome="outcome", strata=["stratum"])
    assert 0.7 < est.ate < 1.3
    assert est.refutations["sign_flips_under_refutation"] <= 1
