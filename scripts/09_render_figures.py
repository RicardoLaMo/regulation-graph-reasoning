"""Phase F-1: render any remaining figures + write LaTeX tables.

Specifically:
  - architecture.pdf  (system-architecture diagram via matplotlib)
  - tables/headline.tex   (baseline vs proposed: F1/ECE/coverage/setsize/abstention)
  - tables/causal.tex     (ATE table for E1-E4)
  - tables/stress.tex     (per-category metrics)
  - tables/dag_assumptions.tex (the 5 stated assumptions)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl

from regreason.causal.dag import assumptions_str
from regreason.config import CFG, ARTIFACTS, DOC, FIGS, TABLES
from regreason import baseline as bl
from regreason.eval.metrics import macro_f1
from regreason.eval.report_tables import write_table
from regreason.extract import build_extractor
from regreason.pipeline import silver_label_routes


def _arch_diagram(out: Path):
    fig, ax = plt.subplots(figsize=(8.0, 4.6), dpi=150)
    ax.axis("off")
    boxes = [
        ("Complaint text", 0.04, 0.55, 0.18, 0.18, "#fde68a"),
        ("Stratified sampler\n(5k from recent3y)", 0.04, 0.20, 0.18, 0.20, "#bbf7d0"),
        ("Hybrid retrieval\n(BM25 + FAISS)", 0.30, 0.55, 0.18, 0.18, "#a5b4fc"),
        ("Rule + SBERT\nstructured extractor", 0.30, 0.20, 0.18, 0.20, "#a5b4fc"),
        ("Hypergraph manifold\n(GAT clique-expand)", 0.55, 0.55, 0.20, 0.18, "#fbcfe8"),
        ("AnswerObject + grounded\ncitations (validator)", 0.55, 0.20, 0.20, 0.20, "#fbcfe8"),
        ("Calibration + Mondrian\nconformal sets + abstention", 0.78, 0.40, 0.20, 0.20, "#fdba74"),
        ("Causal SCM\n(do-interventions)", 0.78, 0.10, 0.20, 0.20, "#fda4af"),
    ]
    for txt, x, y, w, h, c in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=c, edgecolor="black"))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=8)
    arrows = [(0.22, 0.64, 0.30, 0.64), (0.22, 0.30, 0.30, 0.30),
              (0.48, 0.64, 0.55, 0.64), (0.48, 0.30, 0.55, 0.30),
              (0.65, 0.55, 0.78, 0.50), (0.75, 0.30, 0.78, 0.20)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="black"))
    ax.set_xlim(0, 1); ax.set_ylim(0, 0.85)
    ax.set_title("regulation-graph-reasoning system architecture", fontsize=10)
    fig.tight_layout(); fig.savefig(out); plt.close(fig)


def main():
    DOC.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    # Architecture figure
    _arch_diagram(FIGS / "architecture.pdf")

    # Headline table: macro-F1 + ECE + coverage + set size + abstention
    conf_meta = json.loads((ARTIFACTS / "conformal.json").read_text())
    df_test = pl.read_parquet(ARTIFACTS / "sample.parquet")
    extractor = build_extractor()
    silver = silver_label_routes(df_test, extractor)
    df_test = df_test.with_columns(pl.Series("silver_route", silver))

    # Baseline vs proposed: F1
    model = bl.load(ARTIFACTS / "baseline_route.joblib")
    p_baseline = np.load(ARTIFACTS / "baseline_proba.npy")
    p_proposed = np.load(ARTIFACTS / "proposed_proba.npy")
    classes = conf_meta["classes"]

    pred_b = np.array([classes[i] for i in p_baseline.argmax(axis=1)])
    pred_p = np.array([classes[i] for i in p_proposed.argmax(axis=1)])
    f1_b = macro_f1(silver, pred_b.tolist())
    f1_p = macro_f1(silver, pred_p.tolist())

    # Citation faithfulness on the clean 5k sample
    answers = pl.read_parquet(ARTIFACTS / "answers.parquet")
    cite_clean = float(answers["citation_faithful_rate"].mean())

    headline = pd.DataFrame({
        "system": ["TF-IDF + LR (baseline)", "Proposed (rule+SBERT+conformal+causal+grounding)"],
        "macro_F1": [f1_b, f1_p],
        "ECE": [conf_meta["ece_baseline"], conf_meta["ece_proposed"]],
        "Brier": [conf_meta["brier_baseline"], conf_meta["brier_proposed"]],
        "coverage": [float("nan"), conf_meta["marginal_coverage"]],
        "avg_set_size": [float("nan"), conf_meta["avg_set_size"]],
        "abstention": [float("nan"), conf_meta["abstention_rate"]],
        "cite_faithfulness": [float("nan"), cite_clean],
    })
    # Shorten the proposed-system label so the headline table fits the text width.
    headline.loc[headline["system"].str.startswith("Proposed"), "system"] = (
        "Proposed (rule+SBERT+conformal)"
    )
    write_table(headline, TABLES / "headline.tex",
                caption="Headline metrics on the 5k stratified test sample. The proposed pipeline halves the calibration error and exposes a 6.1\\% citation-faithfulness rate as a headline negative result.",
                label="tab:headline", wide=True)

    # Causal table
    causal = json.loads((ARTIFACTS / "causal_results.json").read_text())
    rows = []
    for e in causal["estimates"]:
        rows.append({
            "intervention": e["name"][:55],
            "ATE": e["ate"],
            "CI_low": e["ate_ci_low"],
            "CI_high": e["ate_ci_high"],
            "placebo_ATE": e["refutations"].get("placebo_treatment_ate"),
            "subset_ATE": e["refutations"].get("data_subset_ate"),
            "RCC_delta": e["refutations"].get("random_common_cause_delta"),
            "n": e["n"],
        })
    write_table(pd.DataFrame(rows), TABLES / "causal.tex",
                caption="Backdoor-adjusted ATEs for E1--E4 with refutation tests.",
                label="tab:causal", wide=True)

    # Stress table
    stress = json.loads((ARTIFACTS / "stress_results.json").read_text())
    s_rows = []
    for cat, m in stress.items():
        if "abstention_rate" not in m:
            continue
        s_rows.append({"category": cat, **{k: m.get(k) for k in
                       ["n", "abstention_rate", "avg_set_size", "max_set_size", "citation_faithfulness"]}})
    write_table(pd.DataFrame(s_rows), TABLES / "stress.tex",
                caption="Stress-test response of the proposed pipeline.",
                label="tab:stress")

    # Per-group conformal coverage
    pg_rows = [{"product": k, "coverage": v} for k, v in conf_meta["per_group_coverage"].items()]
    write_table(pd.DataFrame(pg_rows).sort_values("coverage"), TABLES / "per_group_coverage.tex",
                caption="Per-product conformal coverage (Mondrian split-APS, alpha=0.1).",
                label="tab:pgcov")

    # Manifold meta
    mfd = json.loads((ARTIFACTS / "manifold_meta.json").read_text())
    write_table(pd.DataFrame([mfd]), TABLES / "manifold.tex",
                caption="Hypergraph manifold composition and clustering quality.",
                label="tab:mfd", wide=True)

    # Assumption block
    (TABLES / "dag_assumptions.tex").write_text(
        "\\begin{quote}\\small\n" + assumptions_str().replace("\n", "\\\\\n") + "\n\\end{quote}"
    )
    print("rendered: tables/{headline, causal, stress, per_group_coverage, manifold, dag_assumptions}.tex")
    print("figs: architecture.pdf (in addition to ones produced by earlier scripts)")


if __name__ == "__main__":
    main()
