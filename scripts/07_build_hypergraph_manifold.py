"""Phase D: build the complaint↔regulation hypergraph + manifold viz."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import polars as pl

from regreason.config import CFG, ARTIFACTS, FIGS
from regreason.hypergraph_manifold.encoder import encode_hypergraph
from regreason.hypergraph_manifold.incidence import build_incidence
from regreason.hypergraph_manifold.manifold import (
    plot_manifold, silhouette_over_conduct, silhouette_over_labels, umap_project,
)
from regreason.io_loaders import load_regulations


def _embed(texts, encoder=None):
    from sentence_transformers import SentenceTransformer
    if encoder is None:
        encoder = SentenceTransformer(CFG.sbert_model, device=CFG.device)
    return encoder.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True)


def main():
    df_sample = pl.read_parquet(ARTIFACTS / "sample.parquet").to_pandas()
    df_ans = pl.read_parquet(ARTIFACTS / "answers.parquet").to_pandas()
    df_sample["complaint_id"] = df_sample["complaint_id"].astype(str)
    df_ans["complaint_id"] = df_ans["complaint_id"].astype(str)
    df = df_sample.merge(df_ans[["complaint_id", "conducts", "route"]], on="complaint_id", how="inner")
    print(f"complaint nodes: {len(df)}")

    regs = load_regulations()
    print(f"regulation nodes: {len(regs)}")

    print("embedding complaint narratives...")
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(CFG.sbert_model, device=CFG.device)
    c_emb = _embed(df["narrative"].fillna("").tolist(), encoder=encoder)
    print("embedding regulations...")
    r_emb = _embed([f"{r.title}. {r.text}" for r in regs], encoder=encoder)

    print("building hypergraph incidence...")
    hg = build_incidence(
        df, regs, c_emb.astype("float32"), r_emb.astype("float32"),
        product_col="product", conducts_col="conducts", route_col="route",
        complaint_id_col="complaint_id",
    )
    print(f"  hypergraph: N={len(hg.node_ids)} nodes, E={hg.incidence.shape[1]} hyperedges")

    print("encoding via frozen GAT...")
    z = encode_hypergraph(hg, device=CFG.device, seed=CFG.seed, out_dim=128)
    print(f"  GAT output: {z.shape}")

    print("UMAP projection...")
    coords = umap_project(z, n_neighbors=25, min_dist=0.1, metric="cosine", seed=CFG.seed)
    # Silhouettes computed on the high-dim (post-smoothing) embeddings, not the
    # 2-D UMAP coords (UMAP is a viz-only nonlinear projection).
    sil_conduct = silhouette_over_conduct(z, hg.conducts_per_node)
    sil_product = silhouette_over_labels(z, hg.products)
    print(f"  silhouette over conduct (high-dim): {sil_conduct:.4f}")
    print(f"  silhouette over product (high-dim): {sil_product:.4f}")

    out_path = FIGS / "manifold.pdf"
    plot_manifold(coords, hg.node_types, hg.products, out_path,
                  title="Complaint × Regulation Manifold (UMAP over hypergraph smoothing)",
                  silhouette=sil_product)
    np.savez(ARTIFACTS / "manifold.npz",
             coords=coords, types=np.array(hg.node_types), products=np.array(hg.products))
    json.dump({
        "n_nodes": len(hg.node_ids),
        "n_complaints": int(sum(1 for t in hg.node_types if t == "complaint")),
        "n_regs": int(sum(1 for t in hg.node_types if t == "regulation")),
        "n_hyperedges": int(hg.incidence.shape[1]),
        "silhouette_over_conduct": float(sil_conduct),
        "silhouette_over_product": float(sil_product),
    }, open(ARTIFACTS / "manifold_meta.json", "w"), indent=2)
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
