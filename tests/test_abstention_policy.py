"""Regression tests for the two-pronged abstention rule (CCG fix F6)."""
import numpy as np

from regreason.calibrate import AbstentionPolicy


def test_threshold_only_when_set_sizes_omitted():
    ap = AbstentionPolicy(threshold=0.5)
    top1 = np.array([0.6, 0.4, 0.5, 0.49])
    mask = ap.should_abstain(top1)
    assert mask.tolist() == [False, True, False, True]


def test_set_size_clause_fires_independently():
    ap = AbstentionPolicy(threshold=0.45, max_set_size=3)
    top1 = np.array([0.9, 0.9, 0.9, 0.9])
    sizes = np.array([1, 2, 3, 5])
    mask = ap.should_abstain(top1, set_sizes=sizes)
    assert mask.tolist() == [False, False, True, True]


def test_two_pronged_or_semantics():
    ap = AbstentionPolicy(threshold=0.45, max_set_size=3)
    top1 = np.array([0.9, 0.4, 0.8, 0.3])
    sizes = np.array([1, 1, 4, 2])
    mask = ap.should_abstain(top1, set_sizes=sizes)
    assert mask.tolist() == [False, True, True, True]


def test_default_max_set_size_is_three():
    ap = AbstentionPolicy(threshold=0.5)
    assert ap.max_set_size == 3
