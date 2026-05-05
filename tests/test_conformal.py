import numpy as np
from regreason.conformal import MondrianAPSConformal, _aps_set


def test_aps_set_minimum_one_class():
    probs = np.array([0.1, 0.6, 0.3])
    s = _aps_set(probs, q=0.0)
    assert len(s) == 1


def test_mondrian_aps_coverage_recovery():
    rng = np.random.default_rng(0)
    n, K = 600, 4
    classes = ["a", "b", "c", "d"]
    groups = rng.choice(["g1", "g2"], size=n)
    y = rng.choice(classes, size=n)
    probs = rng.dirichlet([1.0] * K, size=n)
    # bias the prob of true class higher
    for i, yy in enumerate(y):
        probs[i, classes.index(yy)] += 0.5
    probs = probs / probs.sum(axis=1, keepdims=True)

    cal_idx = np.arange(0, 300)
    test_idx = np.arange(300, 600)

    conf = MondrianAPSConformal(alpha=0.1)
    conf.fit(probs[cal_idx], y[cal_idx], groups[cal_idx], classes)
    cov = conf.empirical_coverage(probs[test_idx], y[test_idx], groups[test_idx])
    assert cov >= 0.85, f"coverage too low: {cov}"
    assert cov <= 1.0


def test_set_sizes_increase_with_smaller_alpha():
    rng = np.random.default_rng(1)
    n = 400
    probs = rng.dirichlet([0.4, 0.4, 0.4, 0.4], size=n)
    classes = ["a", "b", "c", "d"]
    y = rng.choice(classes, size=n)
    groups = np.array(["g"] * n)
    sizes = []
    for a in [0.30, 0.10, 0.05]:
        c = MondrianAPSConformal(alpha=a)
        c.fit(probs[:200], y[:200], groups[:200], classes)
        sizes.append(c.set_sizes(probs[200:], groups[200:]).mean())
    assert sizes[0] <= sizes[1] + 0.5
    assert sizes[1] <= sizes[2] + 0.5
