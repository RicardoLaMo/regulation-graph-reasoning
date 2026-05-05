"""GAT over the clique expansion of the hypergraph.

Frozen v1: SBERT-init features + 2-layer GAT, no training, deterministic.
Reduces to a learnable feature transform over the joint complaint+regulation graph.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from .incidence import Hypergraph, clique_expand_edges


class HypergraphGAT(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int = 128, out_dim: int = 128, heads: int = 2):
        super().__init__()
        try:
            from torch_geometric.nn import GATConv
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"torch-geometric required: {e}")
        self.gat1 = GATConv(in_dim, hidden_dim, heads=heads, concat=True, dropout=0.0)
        self.gat2 = GATConv(hidden_dim * heads, out_dim, heads=1, concat=False, dropout=0.0)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = self.gat1(x, edge_index)
        h = torch.nn.functional.elu(h)
        h = self.gat2(h, edge_index)
        return h


def _hypergraph_smooth(features: np.ndarray, edge_index: np.ndarray,
                        n_iters: int = 1, alpha: float = 0.5) -> np.ndarray:
    """Lightweight hypergraph smoothing (mean-pool over neighbors, blended with self).

    Uses the clique-expanded adjacency. Per iteration, each node's feature is
    moved toward the mean of its neighbors' features by ``alpha``. This
    preserves the SBERT prior (good for unsupervised manifold viz) while still
    propagating information along the (Conduct, Route) hyperedges.
    """
    if edge_index.shape[1] == 0:
        return features
    src, dst = edge_index[0], edge_index[1]
    N = features.shape[0]
    out = features.copy().astype("float32")
    for _ in range(n_iters):
        agg = np.zeros_like(out)
        deg = np.zeros(N, dtype=np.int64)
        np.add.at(agg, dst, out[src])
        np.add.at(deg, dst, 1)
        deg = np.where(deg == 0, 1, deg)
        agg = agg / deg[:, None]
        out = (1 - alpha) * out + alpha * agg
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        out = out / np.where(norms < 1e-9, 1.0, norms)
    return out


def encode_hypergraph(
    hg: Hypergraph,
    device: str = "cuda:0",
    seed: int = 42,
    out_dim: int = 128,
    use_gat: bool = False,
) -> np.ndarray:
    """Encode the hypergraph into per-node embeddings.

    By default (``use_gat=False``) we apply a one-iteration hypergraph mean
    smoothing over the clique-expanded adjacency, which preserves the SBERT
    prior. Set ``use_gat=True`` for the trainable GATConv-based encoder; with
    random initialization the GAT typically destroys the SBERT manifold, so a
    contrastive fine-tune is recommended before relying on its output.
    """
    if hg.node_features is None or hg.node_features.size == 0:
        raise ValueError("Hypergraph has no node_features; populate with SBERT first")
    edge_index = clique_expand_edges(hg.incidence)

    if not use_gat or edge_index.shape[1] == 0:
        return _hypergraph_smooth(hg.node_features, edge_index, n_iters=1, alpha=0.5)

    torch.manual_seed(seed)
    np.random.seed(seed)
    x = torch.tensor(hg.node_features, dtype=torch.float32, device=device)
    ei = torch.tensor(edge_index, dtype=torch.long, device=device)
    model = HypergraphGAT(
        in_dim=hg.node_features.shape[1], hidden_dim=128, out_dim=out_dim,
    ).to(device)
    model.eval()
    with torch.no_grad():
        z = model(x, ei).detach().cpu().numpy()
    return z
