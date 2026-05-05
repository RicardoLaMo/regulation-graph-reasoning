"""Conflicting evidence: state product=mortgage but narrative is verbatim from credit card complaint."""
from __future__ import annotations

import random
from typing import List

import polars as pl

from .ambiguous import StressExample


def build_conflicting(df: pl.DataFrame, *, n: int = 80, seed: int = 42,
                      text_col: str = "narrative", product_col: str = "product",
                      id_col: str = "complaint_id") -> List[StressExample]:
    rng = random.Random(seed)
    df_pd = df.select([id_col, product_col, text_col]).to_pandas()
    out: List[StressExample] = []
    products = sorted(set(df_pd[product_col].tolist()))
    if len(products) < 2:
        return out
    while len(out) < n and len(df_pd) > 0:
        idx = rng.randrange(0, len(df_pd))
        row = df_pd.iloc[idx]
        narrative = row[text_col] or ""
        if len(narrative) < 80:
            continue
        true_product = row[product_col]
        # claim a different product
        claimed = rng.choice([p for p in products if p != true_product])
        out.append(StressExample(
            text=narrative,
            expected_behavior=f"trust_evidence:product={true_product}",
            source_ids=[str(row[id_col])],
            category="conflicting",
            metadata={"claimed_product": claimed, "true_product": true_product},
        ))
    return out
