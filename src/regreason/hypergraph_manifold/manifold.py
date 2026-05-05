"""UMAP projection + matplotlib visualization of the hypergraph manifold."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np


def umap_project(emb: np.ndarray, *, n_neighbors: int = 25, min_dist: float = 0.1,
                 metric: str = "cosine", seed: int = 42) -> np.ndarray:
    import umap
    reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist,
                        metric=metric, random_state=seed, n_components=2)
    return reducer.fit_transform(emb)


def plot_manifold(coords: np.ndarray, node_types, products, out_path: Path, *,
                  title: str = "Complaint × Regulation Manifold (UMAP over hypergraph GAT)",
                  silhouette: Optional[float] = None) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    coords = np.asarray(coords)
    types = np.asarray(node_types)
    prods = np.asarray(products)

    fig, ax = plt.subplots(figsize=(7.0, 5.5), dpi=150)
    uniq_prods = sorted(set(prods.tolist()))
    cmap = plt.get_cmap("tab20")

    for k, p in enumerate(uniq_prods):
        m_complaint = (prods == p) & (types == "complaint")
        m_reg = (prods == p) & (types == "regulation")
        c = cmap(k % 20)
        if m_complaint.any():
            ax.scatter(coords[m_complaint, 0], coords[m_complaint, 1],
                       s=8, alpha=0.55, marker="o", color=c, label=p[:18])
        if m_reg.any():
            ax.scatter(coords[m_reg, 0], coords[m_reg, 1],
                       s=70, alpha=0.95, marker="^",
                       edgecolors="black", linewidths=0.7, color=c)

    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    cap = title
    if silhouette is not None and not (isinstance(silhouette, float) and silhouette != silhouette):
        cap += f"\n(silhouette over Product = {silhouette:.3f})"
    ax.set_title(cap, fontsize=10)
    ax.legend(fontsize=6, loc="best", ncol=2, frameon=True)
    fig.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def silhouette_over_conduct(coords: np.ndarray, conducts) -> float:
    from sklearn.metrics import silhouette_score
    labels = []
    for cs in conducts:
        if isinstance(cs, str):
            cs = [cs] if cs else []
        labels.append(cs[0] if cs else "_none")
    valid = np.array([l != "_none" for l in labels])
    if valid.sum() < 10 or len(set([l for l in labels if l != "_none"])) < 2:
        return float("nan")
    return float(silhouette_score(coords[valid], np.array(labels)[valid], metric="euclidean"))


def silhouette_over_labels(coords: np.ndarray, labels) -> float:
    from sklearn.metrics import silhouette_score
    arr = np.array([str(x) for x in labels])
    valid = np.array([x not in ("", "None", "nan") for x in arr])
    if valid.sum() < 10 or len(set(arr[valid])) < 2:
        return float("nan")
    return float(silhouette_score(coords[valid], arr[valid], metric="euclidean"))
