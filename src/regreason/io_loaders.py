"""Loaders: complaints (stratified sample), regulations JSON, prebuilt FAISS+BM25 indexes."""
from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import polars as pl

from .config import (
    COMPLAINTS_TEST,
    COMPLAINTS_TRAIN,
    COMPLAINTS_VAL,
    COMPLAINTS_CALIB,
    REGS_JSON,
    COMPLIANCE_INDEXES,
)


@dataclass
class RegSection:
    section_id: str
    regulation: str
    citation: str
    title: str
    text: str
    route_tags: List[str]
    conduct_tags: List[str]


def _detect_text_col(df: pl.DataFrame) -> str:
    for c in ("Consumer complaint narrative", "narrative", "complaint_text", "text", "consumer_narrative"):
        if c in df.columns:
            return c
    raise KeyError(f"no narrative column found; columns: {df.columns[:30]}")


def _detect_product_col(df: pl.DataFrame) -> str:
    for c in ("Product", "product"):
        if c in df.columns:
            return c
    raise KeyError("no Product column found")


def _detect_id_col(df: pl.DataFrame) -> str:
    for c in ("Complaint ID", "complaint_id", "id"):
        if c in df.columns:
            return c
    return None


def _detect_date_col(df: pl.DataFrame) -> Optional[str]:
    for c in ("Date received", "date_received", "date"):
        if c in df.columns:
            return c
    return None


def _detect_issue_col(df: pl.DataFrame) -> Optional[str]:
    for c in ("Issue", "issue"):
        if c in df.columns:
            return c
    return None


def load_complaint_sample(n: int = 5000, seed: int = 42, split: str = "test") -> pl.DataFrame:
    """Stratified sample over (Product, year) buckets from the chosen split."""
    path_map = {
        "test": COMPLAINTS_TEST,
        "train": COMPLAINTS_TRAIN,
        "val": COMPLAINTS_VAL,
        "calibration": COMPLAINTS_CALIB,
    }
    df = pl.read_parquet(path_map[split])
    text_col = _detect_text_col(df)
    prod_col = _detect_product_col(df)
    df = df.filter(
        pl.col(text_col).is_not_null() & (pl.col(text_col).str.len_chars() > 30)
    )
    date_col = _detect_date_col(df)
    if date_col:
        df = df.with_columns(pl.col(date_col).cast(pl.String).str.slice(0, 4).alias("_year"))
        strata = df.group_by([prod_col, "_year"]).agg(pl.len().alias("_count"))
    else:
        df = df.with_columns(pl.lit("0").alias("_year"))
        strata = df.group_by([prod_col, "_year"]).agg(pl.len().alias("_count"))
    total = df.height
    if total == 0:
        return df
    strata = strata.with_columns((pl.col("_count") / total * n).round().cast(pl.Int64).alias("_quota"))
    rng = np.random.default_rng(seed)
    parts = []
    for row in strata.iter_rows(named=True):
        sub = df.filter((pl.col(prod_col) == row[prod_col]) & (pl.col("_year") == row["_year"]))
        take = min(int(row["_quota"]), sub.height)
        if take <= 0:
            continue
        idx = rng.choice(sub.height, size=take, replace=False)
        parts.append(sub[idx.tolist()])
    if parts:
        out = pl.concat(parts).sample(n=min(n, sum(p.height for p in parts)), seed=seed)
    else:
        out = df.sample(n=min(n, df.height), seed=seed)
    if "_year" in out.columns:
        out = out.drop("_year")
    return out.head(n)


def load_regulations(path: Path = REGS_JSON) -> List[RegSection]:
    with open(path, "r") as f:
        data = json.load(f)
    sections = []
    for s in data["sections"]:
        sections.append(
            RegSection(
                section_id=s["id"],
                regulation=s.get("regulation", ""),
                citation=s.get("citation", ""),
                title=s.get("title", ""),
                text=s.get("text", ""),
                route_tags=s.get("route_tags", []),
                conduct_tags=s.get("conduct_tags", []),
            )
        )
    return sections


def load_prebuilt_indexes(indexes_dir: Path = COMPLIANCE_INDEXES) -> dict:
    """Load FAISS, BM25, passage_store, meta from prebuilt artifacts.

    The lifted artifacts use sentence-transformers all-MiniLM-L6-v2 (384-dim).
    """
    indexes_dir = Path(indexes_dir)
    out = {}
    with open(indexes_dir / "passage_store.json") as f:
        out["passages"] = json.load(f)
    with open(indexes_dir / "index_meta.json") as f:
        out["meta"] = json.load(f)
    try:
        with open(indexes_dir / "bm25_index.pkl", "rb") as f:
            out["bm25"] = pickle.load(f)
    except Exception as e:
        out["bm25"] = None
        out["_bm25_err"] = repr(e)
    try:
        with open(indexes_dir / "faiss_index.pkl", "rb") as f:
            out["faiss"] = pickle.load(f)
    except Exception as e:
        out["faiss"] = None
        out["_faiss_err"] = repr(e)
    return out
