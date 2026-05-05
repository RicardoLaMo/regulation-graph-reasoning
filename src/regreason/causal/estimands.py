"""Backdoor-adjusted ATE for E1/E2/E3/E4 with refutation tests.

Avoids DoWhy's heavy stack for our small samples. Instead implements:
  - backdoor adjustment via stratification on (Product, Issue, Conduct)
  - 3 refutation tests:
      * random_common_cause:  add a synthetic random binary common cause
                              with the same marginal as treatment, recompute ATE
      * placebo_treatment:    permute treatment within each stratum, recompute ATE
      * data_subset:           re-estimate on a 70% bootstrap subset
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class CausalEstimate:
    name: str
    ate: float
    ate_ci_low: float
    ate_ci_high: float
    refutations: Dict[str, float]
    n: int


def _stratified_ate(
    df: pd.DataFrame, treatment: str, outcome: str, strata: List[str]
) -> Tuple[float, int]:
    """Average over strata: E[outcome | T=1, strata] - E[outcome | T=0, strata]."""
    df = df.dropna(subset=[treatment, outcome] + strata)
    if df.empty:
        return float("nan"), 0
    diffs: List[Tuple[float, int]] = []
    for _, sub in df.groupby(strata, dropna=False):
        if sub[treatment].nunique() < 2:
            continue
        a = sub.loc[sub[treatment] == 1, outcome].mean()
        b = sub.loc[sub[treatment] == 0, outcome].mean()
        if pd.isna(a) or pd.isna(b):
            continue
        diffs.append((float(a - b), int(len(sub))))
    if not diffs:
        # fall back to marginal
        a = df.loc[df[treatment] == 1, outcome].mean()
        b = df.loc[df[treatment] == 0, outcome].mean()
        return float(a - b) if not (pd.isna(a) or pd.isna(b)) else float("nan"), int(len(df))
    weights = np.array([d[1] for d in diffs], dtype=float)
    vals = np.array([d[0] for d in diffs], dtype=float)
    return float(np.sum(weights * vals) / weights.sum()), int(weights.sum())


def _bootstrap_ci(df: pd.DataFrame, treatment: str, outcome: str, strata: List[str],
                  n_boot: int = 200, seed: int = 0) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    estimates = []
    n = len(df)
    if n < 20:
        return float("nan"), float("nan")
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        ate, _ = _stratified_ate(df.iloc[idx], treatment, outcome, strata)
        if not np.isnan(ate):
            estimates.append(ate)
    if not estimates:
        return float("nan"), float("nan")
    lo = float(np.percentile(estimates, 2.5))
    hi = float(np.percentile(estimates, 97.5))
    return lo, hi


def do_intervention(
    name: str,
    df: pd.DataFrame,
    *,
    treatment: str,
    outcome: str,
    strata: List[str],
    seed: int = 0,
) -> CausalEstimate:
    ate, n = _stratified_ate(df, treatment, outcome, strata)
    lo, hi = _bootstrap_ci(df, treatment, outcome, strata, seed=seed)
    refutations: Dict[str, float] = {}

    rng = np.random.default_rng(seed + 1)
    # 1) random_common_cause
    df_rcc = df.copy()
    df_rcc["_rcc"] = rng.integers(0, 2, size=len(df_rcc))
    ate_rcc, _ = _stratified_ate(df_rcc, treatment, outcome, strata + ["_rcc"])
    refutations["random_common_cause_delta"] = float(abs(ate_rcc - ate))

    # 2) placebo_treatment: permute treatment within strata
    df_p = df.copy()
    perm_treat = []
    for _, sub in df_p.groupby(strata, dropna=False):
        vals = sub[treatment].to_numpy().copy()
        rng.shuffle(vals)
        sub = sub.assign(_perm=vals)
        perm_treat.append(sub)
    if perm_treat:
        df_p = pd.concat(perm_treat)
        ate_pl, _ = _stratified_ate(df_p, "_perm", outcome, strata)
    else:
        ate_pl = 0.0
    refutations["placebo_treatment_ate"] = float(ate_pl)

    # 3) data_subset: 70% bootstrap
    sub_idx = rng.choice(len(df), size=int(0.7 * len(df)), replace=False)
    ate_sub, _ = _stratified_ate(df.iloc[sub_idx], treatment, outcome, strata)
    refutations["data_subset_ate"] = float(ate_sub)
    # Magnitude-aware refutation: a placebo is "passing" if its absolute effect
    # is below 10% of the original ATE magnitude (or below 0.02 if ATE is tiny).
    eps = max(0.02, 0.10 * abs(ate)) if not np.isnan(ate) else 0.02
    refutations["placebo_passes"] = float(abs(ate_pl) < eps)
    refutations["subset_passes"] = float(
        abs(ate_sub - ate) < max(0.02, 0.10 * abs(ate)) if not (np.isnan(ate) or np.isnan(ate_sub)) else False
    )
    refutations["sign_flips_under_refutation"] = float(int(
        not bool(refutations["placebo_passes"]) +
        (not bool(refutations["subset_passes"]) and not np.isnan(ate_sub))
    ))

    return CausalEstimate(
        name=name, ate=ate, ate_ci_low=lo, ate_ci_high=hi,
        refutations=refutations, n=n,
    )


def estimate_to_dict(est: CausalEstimate) -> dict:
    return asdict(est)
