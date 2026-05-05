"""Bootstrap step: stratified 5k complaint sample → artifacts/sample.parquet."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regreason.config import CFG, ARTIFACTS
from regreason.io_loaders import load_complaint_sample, load_regulations, load_prebuilt_indexes


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df = load_complaint_sample(n=CFG.sample_n, seed=CFG.seed, split="test")
    out = ARTIFACTS / "sample.parquet"
    df.write_parquet(out)
    print(f"sample: {df.height} rows -> {out}")

    regs = load_regulations()
    print(f"regulations: {len(regs)} sections")

    idx = load_prebuilt_indexes()
    print(f"prebuilt indexes meta: {idx['meta']}, passages={len(idx['passages'])}")
    if idx.get("faiss") is None:
        print(f"  NOTE: faiss pickle did not load (lifted-class issue): {idx.get('_faiss_err')}")
        print(f"  HybridSearcher will rebuild FAISS over the 51 sections at first use (fast).")


if __name__ == "__main__":
    main()
