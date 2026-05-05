"""Ambiguous narratives: concatenate first half of A with second half of B (different products)."""
from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Iterable, List

import polars as pl


@dataclass
class StressExample:
    text: str
    expected_behavior: str        # "abstain" | "set_includes:<...>"
    source_ids: list
    category: str
    metadata: dict


def build_ambiguous(df: pl.DataFrame, *, n: int = 80, seed: int = 42,
                    text_col: str = "narrative", product_col: str = "product",
                    id_col: str = "complaint_id") -> List[StressExample]:
    rng = random.Random(seed)
    products = sorted(set(df[product_col].to_list()))
    out: List[StressExample] = []
    df_pd = df.select([id_col, product_col, text_col]).to_pandas()
    by_prod = {p: df_pd[df_pd[product_col] == p].reset_index(drop=True) for p in products}
    pairs = []
    for p1 in products:
        for p2 in products:
            if p1 == p2:
                continue
            pairs.append((p1, p2))
    rng.shuffle(pairs)
    while len(out) < n:
        if not pairs:
            break
        p1, p2 = pairs.pop()
        a = by_prod[p1]
        b = by_prod[p2]
        if a.empty or b.empty:
            continue
        ra = a.iloc[rng.randrange(0, len(a))]
        rb = b.iloc[rng.randrange(0, len(b))]
        ta = (ra[text_col] or "")[: max(60, len(ra[text_col] or "") // 2)]
        tb = (rb[text_col] or "")[max(60, len(rb[text_col] or "") // 2):]
        text = f"{ta} {tb}".strip()
        if len(text) < 80:
            continue
        out.append(StressExample(
            text=text,
            expected_behavior="abstain_or_set_size>=2",
            source_ids=[str(ra[id_col]), str(rb[id_col])],
            category="ambiguous",
            metadata={"product_a": p1, "product_b": p2},
        ))
    return out
