"""Temperature scaling, Platt-style scaling for scalar confidences, abstention."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F


@dataclass
class TemperatureScaler:
    """Single scalar temperature T fitted by minimizing NLL on (logits, labels)."""
    T: float = 1.0

    def fit(self, logits: np.ndarray, labels: np.ndarray, *, lr: float = 0.01,
            max_iter: int = 200, device: str = "cpu") -> "TemperatureScaler":
        L = torch.tensor(logits, dtype=torch.float32, device=device)
        y = torch.tensor(labels, dtype=torch.long, device=device)
        T = torch.nn.Parameter(torch.tensor(1.0, device=device))
        opt = torch.optim.LBFGS([T], lr=lr, max_iter=max_iter)

        def closure():
            opt.zero_grad()
            scaled = L / T.clamp(min=1e-3)
            loss = F.cross_entropy(scaled, y)
            loss.backward()
            return loss

        opt.step(closure)
        self.T = float(T.detach().clamp(min=1e-3).cpu().item())
        return self

    def transform(self, logits: np.ndarray) -> np.ndarray:
        L = logits / max(self.T, 1e-3)
        z = L - L.max(axis=1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)


@dataclass
class PlattScaler:
    """1-D Platt: p = 1/(1+exp(a*x+b)) for scalar score x against binary correct/incorrect."""
    a: float = -1.0
    b: float = 0.0

    def fit(self, scores: np.ndarray, correct: np.ndarray) -> "PlattScaler":
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression()
        lr.fit(scores.reshape(-1, 1), correct.astype(int))
        self.a = float(lr.coef_[0][0])
        self.b = float(lr.intercept_[0])
        return self

    def transform(self, scores: np.ndarray) -> np.ndarray:
        x = self.a * scores + self.b
        return 1.0 / (1.0 + np.exp(-x))


@dataclass
class AbstentionPolicy:
    """Abstain when top-1 calibrated prob < threshold OR conformal set is too wide.

    Two-pronged rule from the report and plan: abstention fires under either
    low single-class confidence or high conformal hedging. Earlier revisions
    only applied the threshold half of the rule, producing a headline
    abstention rate inconsistent with the reported set-size distribution.
    """
    threshold: float = 0.5
    max_set_size: int = 3

    def should_abstain(self, top1_prob: np.ndarray,
                       set_sizes: Optional[np.ndarray] = None) -> np.ndarray:
        cond_top1 = top1_prob < self.threshold
        if set_sizes is None:
            return cond_top1
        return cond_top1 | (np.asarray(set_sizes) >= self.max_set_size)
