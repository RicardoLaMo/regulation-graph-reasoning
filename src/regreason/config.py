"""Centralized paths, seeds, and hyperparameters."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
DOC = ROOT / "doc"
FIGS = DOC / "figs"
TABLES = DOC / "tables"

# HF cache lookup: prefer local snapshot path when offline mode is in effect
_HF_HUB = Path(os.environ.get("HUGGINGFACE_HUB_CACHE", os.path.expanduser("~/hf_cache/hub")))


def _resolve_sbert_path(repo_id: str) -> str:
    folder = _HF_HUB / f"models--{repo_id.replace('/', '--')}"
    snaps = folder / "snapshots"
    if snaps.exists():
        for s in sorted(snaps.iterdir()):
            if (s / "config.json").exists():
                return str(s)
    return repo_id

COMPLAINTS_TRAIN = DATA / "recent3y" / "train.parquet"
COMPLAINTS_VAL = DATA / "recent3y" / "val.parquet"
COMPLAINTS_TEST = DATA / "recent3y" / "test.parquet"
COMPLAINTS_CALIB = DATA / "recent3y" / "calibration.parquet"
REGS_JSON = DATA / "compliance" / "cfpb_regulations.json"
COMPLIANCE_INDEXES = DATA / "compliance_indexes"


@dataclass
class Config:
    seed: int = 42
    sample_n: int = 5000
    alpha: float = 0.1                      # 1 - target coverage
    abstain_threshold: float = 0.45         # top-1 prob below this -> abstain
    sbert_model: str = _resolve_sbert_path("sentence-transformers/all-MiniLM-L6-v2")
    device: str = "cuda:0"                  # avoid GPU 3 (occupied)
    train_gat: bool = False                 # frozen GAT in v1
    top_k_retrieval: int = 5
    bm25_alpha: float = 0.5                 # weight for BM25 vs FAISS in hybrid
    stress_n_per_category: int = 80


CFG = Config()
