"""Phase C-1: fit temperature scaling on baseline + Mondrian split-conformal sets.

Inputs:
  - baseline_route.joblib (trained on silver routes from train.parquet)
  - calibration.parquet (separate temporal split; we silver-label routes at runtime)
  - sample.parquet (5k stratified test sample)

Outputs:
  - artifacts/conformal.json: per-group quantiles, marginal coverage, avg set size.
  - artifacts/proposed_proba.npy + artifacts/baseline_proba.npy
  - doc/figs/coverage_vs_alpha.pdf, reliability.pdf, setsize_hist.pdf
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from regreason import baseline as bl
from regreason.config import CFG, ARTIFACTS, FIGS, COMPLAINTS_CALIB
from regreason.calibrate import TemperatureScaler, AbstentionPolicy
from regreason.conformal import MondrianAPSConformal
from regreason.eval.metrics import (
    expected_calibration_error, brier_score, abstention_rate, accuracy_given_not_abstained,
)
from regreason.extract import build_extractor
from regreason.io_loaders import load_complaint_sample
from regreason.pipeline import silver_label_routes


def main():
    print("loading trained baseline...")
    model = bl.load(ARTIFACTS / "baseline_route.joblib")
    classes = list(model.classes_)
    print(f"  classes={classes}")

    print("loading calibration parquet (small) and sample...")
    extractor = build_extractor()
    df_cal = load_complaint_sample(n=2000, seed=CFG.seed, split="calibration")
    routes_cal = silver_label_routes(df_cal, extractor)
    df_cal = df_cal.with_columns(pl.Series("silver_route", routes_cal))
    df_test = pl.read_parquet(ARTIFACTS / "sample.parquet")
    routes_test = silver_label_routes(df_test, extractor)
    df_test = df_test.with_columns(pl.Series("silver_route", routes_test))

    print("baseline probabilities on calibration & test...")
    p_cal = bl.predict_proba(model, df_cal["narrative"].to_list())
    p_test = bl.predict_proba(model, df_test["narrative"].to_list())

    # Temperature scaling needs logits; LR predict_proba returns probs.
    # Use log(p) as a proxy logit for calibration, then re-softmax.
    eps = 1e-9
    logits_cal = np.log(np.clip(p_cal, eps, 1.0))
    logits_test = np.log(np.clip(p_test, eps, 1.0))
    cls_to_idx = {c: i for i, c in enumerate(classes)}
    y_cal = np.array([cls_to_idx[r] for r in df_cal["silver_route"].to_list()])
    ts = TemperatureScaler().fit(logits_cal, y_cal)
    print(f"  T = {ts.T:.3f}")
    p_cal_t = ts.transform(logits_cal)
    p_test_t = ts.transform(logits_test)

    np.save(ARTIFACTS / "baseline_proba.npy", p_test)
    np.save(ARTIFACTS / "proposed_proba.npy", p_test_t)

    print("Mondrian split conformal (APS) by Product...")
    groups_cal = np.array(df_cal["product"].to_list(), dtype=object)
    groups_test = np.array(df_test["product"].to_list(), dtype=object)
    conf = MondrianAPSConformal(alpha=CFG.alpha)
    conf.fit(p_cal_t, np.array(df_cal["silver_route"]), groups_cal, classes)
    sets = conf.predict_set(p_test_t, groups_test)
    set_sizes = np.array([len(s) for s in sets])
    cov = conf.empirical_coverage(p_test_t, np.array(df_test["silver_route"]), groups_test)

    per_group_cov = {}
    for g in np.unique(groups_test):
        mask = (groups_test == g)
        if mask.sum() == 0:
            continue
        sub_sets = [sets[i] for i in np.where(mask)[0]]
        sub_y = np.array(df_test["silver_route"])[mask]
        per_group_cov[str(g)] = float(np.mean([y in s for s, y in zip(sub_sets, sub_y)]))

    # Abstention: |S| >= 3 OR top1 < theta (matches report & plan)
    abs_pol = AbstentionPolicy(threshold=CFG.abstain_threshold, max_set_size=3)
    abstain = abs_pol.should_abstain(p_test_t.max(axis=1), set_sizes=set_sizes)
    pred_idx = p_test_t.argmax(axis=1)
    pred = np.array([classes[i] for i in pred_idx])
    abst_rate = abstention_rate(abstain)
    acc_keep = accuracy_given_not_abstained(df_test["silver_route"].to_list(), pred.tolist(), abstain)

    # ECE / Brier
    ece_b = expected_calibration_error(p_test, np.array(df_test["silver_route"]), classes)
    ece_p = expected_calibration_error(p_test_t, np.array(df_test["silver_route"]), classes)
    bs_b = brier_score(p_test, np.array(df_test["silver_route"]), classes)
    bs_p = brier_score(p_test_t, np.array(df_test["silver_route"]), classes)

    out = {
        "T": ts.T,
        "alpha": CFG.alpha,
        "marginal_coverage": cov,
        "avg_set_size": float(np.mean(set_sizes)),
        "per_group_coverage": per_group_cov,
        "abstention_rate": abst_rate,
        "accuracy_given_not_abstained": acc_keep,
        "ece_baseline": ece_b,
        "ece_proposed": ece_p,
        "brier_baseline": bs_b,
        "brier_proposed": bs_p,
        "n_test": int(p_test.shape[0]),
        "classes": classes,
    }
    (ARTIFACTS / "conformal.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

    # Figures
    FIGS.mkdir(parents=True, exist_ok=True)

    # 1) coverage vs alpha
    alphas = np.linspace(0.02, 0.30, 15)
    covs = []
    for a in alphas:
        c = MondrianAPSConformal(alpha=float(a))
        c.fit(p_cal_t, np.array(df_cal["silver_route"]), groups_cal, classes)
        covs.append(c.empirical_coverage(p_test_t, np.array(df_test["silver_route"]), groups_test))
    fig, ax = plt.subplots(figsize=(5.5, 3.8), dpi=150)
    ax.plot(alphas, [1 - a for a in alphas], "k--", label="target  $1-\\alpha$")
    ax.plot(alphas, covs, "o-", label="empirical")
    ax.set_xlabel("$\\alpha$"); ax.set_ylabel("coverage")
    ax.set_title("Mondrian APS coverage vs $\\alpha$"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIGS / "coverage_vs_alpha.pdf"); plt.close(fig)

    # 2) reliability
    fig, ax = plt.subplots(1, 2, figsize=(8.5, 3.8), dpi=150, sharey=True)
    for a, p, ttl in [(ax[0], p_test, "baseline"), (ax[1], p_test_t, "+ temperature")]:
        conf = p.max(axis=1)
        pred_i = p.argmax(axis=1)
        y_idx = np.array([cls_to_idx[r] for r in df_test["silver_route"]])
        correct = (pred_i == y_idx).astype(float)
        bins = np.linspace(0, 1, 11)
        bin_acc, bin_conf, weights = [], [], []
        for i in range(10):
            m = (conf > bins[i]) & (conf <= bins[i+1] + (1e-9 if i==9 else 0))
            if m.sum() > 0:
                bin_acc.append(correct[m].mean()); bin_conf.append(conf[m].mean()); weights.append(m.sum())
        a.plot([0, 1], [0, 1], "k--")
        a.bar(bin_conf, bin_acc, width=0.08, alpha=0.7, edgecolor="black")
        a.set_xlabel("predicted prob"); a.set_title(ttl); a.grid(alpha=0.3)
    ax[0].set_ylabel("empirical accuracy")
    fig.suptitle("Reliability diagrams (route classification)")
    fig.tight_layout(); fig.savefig(FIGS / "reliability.pdf"); plt.close(fig)

    # 3) set-size histogram
    fig, ax = plt.subplots(figsize=(5, 3.5), dpi=150)
    ax.hist(set_sizes, bins=range(1, max(set_sizes) + 2), edgecolor="black", alpha=0.8)
    ax.set_xlabel("conformal set size"); ax.set_ylabel("# complaints")
    ax.set_title(f"Conformal set sizes (alpha={CFG.alpha}, mean={set_sizes.mean():.2f})")
    fig.tight_layout(); fig.savefig(FIGS / "setsize_hist.pdf"); plt.close(fig)

    print("figures: coverage_vs_alpha.pdf, reliability.pdf, setsize_hist.pdf")


if __name__ == "__main__":
    main()
