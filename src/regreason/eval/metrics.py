"""Aggregate metrics: F1, ECE, Brier, conformal coverage, set-size, abstention, citation faithfulness."""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.metrics import f1_score, log_loss


def macro_f1(y_true: Sequence, y_pred: Sequence) -> float:
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def expected_calibration_error(probs: np.ndarray, y_true: np.ndarray, classes: Sequence,
                               n_bins: int = 15) -> float:
    cls_to_idx = {c: i for i, c in enumerate(classes)}
    y_idx = np.array([cls_to_idx[str(y)] for y in y_true])
    conf = probs.max(axis=1)
    pred_idx = probs.argmax(axis=1)
    correct = (pred_idx == y_idx).astype(float)
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(probs)
    for i in range(n_bins):
        mask = (conf > bins[i]) & (conf <= bins[i + 1] + (1e-9 if i == n_bins - 1 else 0))
        if mask.sum() == 0:
            continue
        bin_acc = correct[mask].mean()
        bin_conf = conf[mask].mean()
        ece += (mask.sum() / n) * abs(bin_acc - bin_conf)
    return float(ece)


def brier_score(probs: np.ndarray, y_true: np.ndarray, classes: Sequence) -> float:
    cls_to_idx = {c: i for i, c in enumerate(classes)}
    y_idx = np.array([cls_to_idx[str(y)] for y in y_true])
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(len(probs)), y_idx] = 1.0
    return float(((probs - one_hot) ** 2).sum(axis=1).mean())


def empirical_coverage(sets: List[List[str]], y_true: Sequence) -> float:
    y_true = [str(y) for y in y_true]
    hits = sum(1 for s, y in zip(sets, y_true) if y in s)
    return hits / max(1, len(y_true))


def avg_set_size(sets: List[List[str]]) -> float:
    if not sets:
        return 0.0
    return float(np.mean([len(s) for s in sets]))


def abstention_rate(abstain_mask: np.ndarray) -> float:
    if len(abstain_mask) == 0:
        return 0.0
    return float(np.mean(abstain_mask.astype(bool)))


def accuracy_given_not_abstained(y_true: Sequence, y_pred: Sequence,
                                 abstain_mask: np.ndarray) -> float:
    y_true = np.array([str(y) for y in y_true])
    y_pred = np.array([str(y) for y in y_pred])
    keep = ~abstain_mask.astype(bool)
    if keep.sum() == 0:
        return float("nan")
    return float((y_pred[keep] == y_true[keep]).mean())


def citation_faithfulness(records: Iterable) -> float:
    """records: iterable of {'faithful': bool}; returns share faithful."""
    arr = [bool(r.get("faithful", False)) for r in records]
    if not arr:
        return float("nan")
    return float(np.mean(arr))


def safe_log_loss(probs: np.ndarray, y_true: Sequence, classes: Sequence) -> float:
    try:
        return float(log_loss(y_true, probs, labels=list(classes)))
    except Exception:
        return float("nan")
