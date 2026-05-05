"""Phase B-1: train the TF-IDF + LogReg baseline on silver routes from train.parquet.

The baseline lacks (a) causal reasoning, (b) conformal sets, (c) grounded
citations — by construction. It exists so the proposed system has something
to compete against.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import polars as pl

from regreason import baseline as bl
from regreason.config import CFG, ARTIFACTS, COMPLAINTS_TRAIN
from regreason.extract import build_extractor
from regreason.io_loaders import load_complaint_sample
from regreason.pipeline import silver_label_routes


MAX_TRAIN = 12_000


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    print(f"loading {MAX_TRAIN} rows from train.parquet ...")
    t0 = time.time()
    df = load_complaint_sample(n=MAX_TRAIN, seed=CFG.seed, split="train")
    print(f"  loaded {df.height} rows in {time.time()-t0:.1f}s")

    print("building extractor (SBERT canonical phrases)...")
    extractor = build_extractor()

    print("silver-labeling routes via rule-based extractor...")
    t0 = time.time()
    routes = silver_label_routes(df, extractor)
    df = df.with_columns(pl.Series("silver_route", routes))
    print(f"  done in {time.time()-t0:.1f}s; route counts: {df['silver_route'].value_counts().to_dict(as_series=False)}")

    texts = df["narrative"].to_list()
    print("training calibrated LR baseline (5-fold sigmoid)...")
    t0 = time.time()
    model = bl.train_route_baseline(texts, routes)
    print(f"  trained in {time.time()-t0:.1f}s; classes: {model.classes_}")

    out = ARTIFACTS / "baseline_route.joblib"
    bl.save(model, out)
    meta = {"n_train": len(texts), "classes": list(model.classes_)}
    (ARTIFACTS / "baseline_route_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
