"""Counterfactual twin generators: do(EvidenceGroundedness=0|1), do(Conduct=...)."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import polars as pl

from ..ontology import ConductType, CONDUCT_PHRASES


def do_drop_evidence(df: pl.DataFrame) -> pl.DataFrame:
    """do(EvidenceGroundedness=0): mark a column instructing downstream not to ground."""
    return df.with_columns(pl.lit(0.0).alias("evidence_groundedness"))


def do_oracle_evidence(df: pl.DataFrame) -> pl.DataFrame:
    """do(EvidenceGroundedness=1): mark for oracle grounding (top-1 of the gold reg-section)."""
    return df.with_columns(pl.lit(1.0).alias("evidence_groundedness"))


def do_set_conduct(df: pl.DataFrame, text_col: str, target_conduct: ConductType,
                   max_subs: int = 1) -> pl.DataFrame:
    """do(Conduct = target_conduct): regex-replace the *first* trigger phrase from
    a different conduct with one of the target's canonical phrases. Returns a new
    DataFrame with the modified narrative."""
    target_phrase = CONDUCT_PHRASES[target_conduct][0]

    def _swap(t: str) -> str:
        if t is None:
            return t
        # try replacing any non-target trigger phrase with a target phrase
        replaced = 0
        s = t
        for c, phrases in CONDUCT_PHRASES.items():
            if c == target_conduct:
                continue
            for p in phrases:
                if p.lower() in s.lower():
                    # do a case-insensitive replace once
                    idx = s.lower().find(p.lower())
                    s = s[:idx] + target_phrase + s[idx + len(p):]
                    replaced += 1
                    if replaced >= max_subs:
                        return s
        # no trigger found: prepend the target phrase
        return f"{target_phrase}. {s}"

    return df.with_columns(
        pl.col(text_col).map_elements(_swap, return_dtype=pl.String).alias(text_col)
    )


def counterfactual_twins(df: pl.DataFrame, *, text_col: str = "narrative") -> Dict[str, pl.DataFrame]:
    """Returns a dict of intervention_name -> twin_df."""
    return {
        "do_evidence=0": do_drop_evidence(df),
        "do_evidence=1": do_oracle_evidence(df),
        "do_conduct=deceptive_practice": do_set_conduct(df, text_col, ConductType.DECEPTIVE_PRACTICE),
        "do_severity=max": df.with_columns(pl.lit(5).alias("do_severity")),
    }
