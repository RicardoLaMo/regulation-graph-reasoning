import polars as pl

from regreason.stress.adversarial import build_adversarial
from regreason.stress.ambiguous import build_ambiguous
from regreason.stress.conflicting import build_conflicting


def _fake_df(n=100):
    products = ["Credit card", "Mortgage", "Debt collection", "Credit reporting"]
    rows = []
    for i in range(n):
        rows.append({
            "complaint_id": f"c{i}",
            "product": products[i % len(products)],
            "narrative": f"a complaint {i} about {products[i % len(products)].lower()} where unauthorized fees were charged repeatedly",
        })
    return pl.DataFrame(rows)


def test_ambiguous_generates_examples():
    df = _fake_df()
    out = build_ambiguous(df, n=20, seed=0)
    assert 5 <= len(out) <= 20
    assert all(o.category == "ambiguous" for o in out)
    assert all(len(o.text) >= 80 for o in out)


def test_conflicting_examples():
    df = _fake_df()
    out = build_conflicting(df, n=20, seed=0)
    assert 1 <= len(out) <= 20
    assert all(o.category == "conflicting" for o in out)
    assert all(o.metadata["claimed_product"] != o.metadata["true_product"] for o in out)


def test_adversarial_examples():
    df = _fake_df()
    out = build_adversarial(df, n=24, seed=0)
    assert len(out) >= 4
    cats = {o.category.split(":", 1)[1] for o in out}
    assert cats.issubset({"prompt_injection", "citation_hallucination", "paraphrase", "negation_flip"})
    pi = [o for o in out if o.category.endswith("prompt_injection")]
    assert any("IGNORE PRIOR INSTRUCTIONS" in o.text for o in pi)
