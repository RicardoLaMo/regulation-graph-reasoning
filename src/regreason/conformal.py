"""Mondrian split-conformal (APS) prediction sets.

Calibration: per-group quantile of APS nonconformity scores.
Inference: smallest set (in decreasing prob order) whose cumulative prob >= q̂_g.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np


def _aps_nonconformity_for_true(probs: np.ndarray, y_idx: np.ndarray) -> np.ndarray:
    """For each row, sum of probs of classes ranked >= true class (descending)."""
    order = np.argsort(-probs, axis=1)
    n, K = probs.shape
    sorted_probs = np.take_along_axis(probs, order, axis=1)
    cum = np.cumsum(sorted_probs, axis=1)
    pos = np.zeros(n, dtype=int)
    for i in range(n):
        # rank position of true class
        pos[i] = int(np.where(order[i] == y_idx[i])[0][0])
    return cum[np.arange(n), pos]


def _aps_set(probs_row: np.ndarray, q: float) -> List[int]:
    order = np.argsort(-probs_row)
    cum = 0.0
    out: List[int] = []
    for c in order:
        cum += float(probs_row[c])
        out.append(int(c))
        if cum >= q:
            break
    return out


@dataclass
class MondrianAPSConformal:
    alpha: float = 0.1
    quantiles: Dict[str, float] = field(default_factory=dict)
    classes_: List[str] = field(default_factory=list)
    default_q: float = 1.0

    def fit(self, probs: np.ndarray, labels: np.ndarray, groups: np.ndarray,
            classes: List[str]) -> "MondrianAPSConformal":
        self.classes_ = list(classes)
        cls_to_idx = {c: i for i, c in enumerate(classes)}
        y_idx = np.array([cls_to_idx[str(y)] for y in labels])
        s = _aps_nonconformity_for_true(probs, y_idx)
        self.quantiles = {}
        for g in np.unique(groups):
            mask = (groups == g)
            n_g = int(mask.sum())
            if n_g < 5:
                continue
            level = np.ceil((n_g + 1) * (1 - self.alpha)) / n_g
            level = float(min(1.0, level))
            self.quantiles[str(g)] = float(np.quantile(s[mask], level, method="higher"))
        if s.size:
            level = np.ceil((s.size + 1) * (1 - self.alpha)) / s.size
            self.default_q = float(np.quantile(s, min(1.0, level), method="higher"))
        return self

    def predict_set(self, probs: np.ndarray, groups: np.ndarray) -> List[List[str]]:
        out: List[List[str]] = []
        for i in range(probs.shape[0]):
            g = str(groups[i])
            q = self.quantiles.get(g, self.default_q)
            idx = _aps_set(probs[i], q)
            out.append([self.classes_[j] for j in idx])
        return out

    def set_sizes(self, probs: np.ndarray, groups: np.ndarray) -> np.ndarray:
        return np.array([len(s) for s in self.predict_set(probs, groups)])

    def empirical_coverage(self, probs: np.ndarray, labels: np.ndarray, groups: np.ndarray) -> float:
        sets = self.predict_set(probs, groups)
        labels = [str(y) for y in labels]
        hits = sum(1 for s, y in zip(sets, labels) if y in s)
        return hits / max(1, len(labels))
