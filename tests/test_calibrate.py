import numpy as np
from regreason.calibrate import TemperatureScaler, AbstentionPolicy, PlattScaler


def test_temperature_scaler_reduces_overconfidence():
    rng = np.random.default_rng(0)
    n, K = 1000, 4
    y = rng.integers(0, K, size=n)
    # Construct overconfident-but-wrong predictions: predicted argmax is (y+1)%K
    # with high logit, true class has small logit. Calibrating should learn T > 1.
    logits = rng.standard_normal((n, K)) * 0.3
    wrong_idx = (y + 1) % K
    logits[np.arange(n), wrong_idx] += 6.0
    ts = TemperatureScaler().fit(logits, y)
    # T should grow large to flatten the misplaced confidence
    assert ts.T > 1.5


def test_abstention_policy_threshold():
    p = AbstentionPolicy(threshold=0.5)
    top1 = np.array([0.9, 0.45, 0.7, 0.4])
    abs_mask = p.should_abstain(top1)
    assert abs_mask.tolist() == [False, True, False, True]


def test_platt_scaler_monotonic():
    scores = np.linspace(-3, 3, 100)
    correct = (scores > 0).astype(int)
    p = PlattScaler().fit(scores, correct)
    transformed = p.transform(scores)
    assert np.all(np.diff(transformed) >= -1e-6) or np.all(np.diff(transformed) <= 1e-6)
