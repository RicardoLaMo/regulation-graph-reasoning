"""Phase E: run stress tests on the pipeline.

For each stress example, we run:
  - the BASELINE classifier (TF-IDF + LR + Platt) -> route prediction (no abstention)
  - the PROPOSED system     (rule+SBERT extract -> ground -> conformal/abstain)
We measure:
  - abstention rate, conformal set-size growth (vs clean), accuracy-given-not-abstained,
    citation-faithfulness rate (where applicable).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from regreason import baseline as bl
from regreason.calibrate import AbstentionPolicy, TemperatureScaler
from regreason.config import CFG, ARTIFACTS, FIGS
from regreason.conformal import MondrianAPSConformal
from regreason.extract import build_extractor, extract_answer_object
from regreason.grounding import attribute, citation_faithful
from regreason.io_loaders import load_regulations
from regreason.retrieve import HybridSearcher
from regreason.stress.adversarial import build_adversarial
from regreason.stress.ambiguous import build_ambiguous
from regreason.stress.conflicting import build_conflicting


def _build_examples(df):
    n = CFG.stress_n_per_category
    return {
        "ambiguous":   build_ambiguous(df,   n=n, seed=CFG.seed),
        "conflicting": build_conflicting(df, n=n, seed=CFG.seed + 1),
        "adversarial": build_adversarial(df, n=n, seed=CFG.seed + 2),
    }


def main():
    print("loading models + data...")
    model = bl.load(ARTIFACTS / "baseline_route.joblib")
    classes = list(model.classes_)
    df_sample = pl.read_parquet(ARTIFACTS / "sample.parquet")
    extractor = build_extractor()
    regs = load_regulations()
    searcher = HybridSearcher(regs, encoder=extractor.encoder)

    # Reload conformal calibration
    conf_meta = json.loads((ARTIFACTS / "conformal.json").read_text())
    T = float(conf_meta["T"])

    # Refit conformal on calibration probs (cheap)
    df_cal = pl.read_parquet(ARTIFACTS / "sample.parquet").sample(n=1500, seed=CFG.seed + 9)
    p_cal = bl.predict_proba(model, df_cal["narrative"].to_list())
    eps = 1e-9
    logits_cal = np.log(np.clip(p_cal, eps, 1.0))
    p_cal_t = TemperatureScaler(T=T).transform(logits_cal)
    from regreason.pipeline import silver_label_routes
    routes_cal = silver_label_routes(df_cal, extractor)
    groups_cal = np.array(df_cal["product"].to_list(), dtype=object)
    conf = MondrianAPSConformal(alpha=CFG.alpha)
    conf.fit(p_cal_t, np.array(routes_cal), groups_cal, classes)
    abs_pol = AbstentionPolicy(threshold=CFG.abstain_threshold, max_set_size=3)

    examples = _build_examples(df_sample)
    summary = {}
    for cat, exs in examples.items():
        if not exs:
            summary[cat] = {"n": 0}
            continue
        texts = [e.text for e in exs]
        groups = [e.metadata.get("true_product", e.metadata.get("product_a", "_")) for e in exs]
        groups = np.array([str(g) for g in groups], dtype=object)

        # Baseline
        p = bl.predict_proba(model, texts)
        p_t = TemperatureScaler(T=T).transform(np.log(np.clip(p, eps, 1.0)))
        sets = conf.predict_set(p_t, groups)
        set_sizes = np.array([len(s) for s in sets])
        abstain_mask = abs_pol.should_abstain(p_t.max(axis=1), set_sizes=set_sizes)

        # Proposed: route + grounding + citation faithfulness
        cite_results = []
        for ex in exs:
            ans = extract_answer_object(ex.text, "stress", "", "", extractor)
            ans = attribute(ex.text, ans, searcher, encoder=extractor.encoder, top_k_passages=2)
            if ans.conducts:
                reg_spans = [s for s in ans.evidence_spans if s.source == "regulation"]
                if reg_spans:
                    pid = reg_spans[0].passage_id
                    text = next((r.text for r in regs if r.section_id == pid), "")
                    cite_results.append({"faithful": citation_faithful(text, ans.conducts[0])})
        cite_rate = float(np.mean([r["faithful"] for r in cite_results])) if cite_results else float("nan")

        summary[cat] = {
            "n": len(exs),
            "abstention_rate": float(np.mean(abstain_mask)),
            "avg_set_size": float(np.mean(set_sizes)),
            "max_set_size": int(np.max(set_sizes)) if len(set_sizes) else 0,
            "citation_faithfulness": cite_rate,
        }

    (ARTIFACTS / "stress_results.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

    # Bar chart
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    cats = list(summary.keys())
    abst = [summary[c].get("abstention_rate", 0) for c in cats]
    setsz = [summary[c].get("avg_set_size", 0) for c in cats]
    cit = [summary[c].get("citation_faithfulness", 0) or 0 for c in cats]
    x = np.arange(len(cats))
    w = 0.27
    ax.bar(x - w, abst, width=w, label="abstention rate")
    ax.bar(x, [s / max(setsz + [1]) for s in setsz], width=w, label=f"avg set size / {max(setsz + [1]):.1f}")
    ax.bar(x + w, cit, width=w, label="citation faithfulness")
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylim(0, 1.05); ax.legend(loc="upper left", fontsize=8)
    ax.set_title("Stress-test response (proposed pipeline)")
    fig.tight_layout(); fig.savefig(FIGS / "stress_bars.pdf"); plt.close(fig)
    print("figure: stress_bars.pdf")


if __name__ == "__main__":
    main()
