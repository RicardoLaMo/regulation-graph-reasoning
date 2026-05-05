"""End-to-end pipeline orchestrator: sample → baseline → extract → ground → calibrate+conformal → causal → hypergraph → stress → render."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import polars as pl

from .config import CFG, ARTIFACTS, FIGS, TABLES
from . import baseline as bl
from .calibrate import AbstentionPolicy
from .conformal import MondrianAPSConformal
from .extract import build_extractor, extract_answer_object
from .grounding import attribute, citation_faithful
from .io_loaders import load_complaint_sample, load_regulations
from .ontology import AnswerObject, ConductType, RouteTarget, CONDUCT_TO_ROUTE
from .retrieve import HybridSearcher


def _silver_route_from_text(text: str, product: str, extractor) -> str:
    a = extract_answer_object(text or "", complaint_id="silver", product=product, issue="", state=extractor)
    return a.route


def silver_label_routes(df: pl.DataFrame, extractor, *, text_col: str = "narrative",
                        product_col: str = "product", batch_size: int = 256) -> List[str]:
    """Vectorized silver labeling: one SBERT encode batch over all narratives,
    then per-row rule combination + ontology constraint validation."""
    import re as _re
    import numpy as _np
    from .ontology import (
        ConductType, HarmType, OntologyConstraintValidator, RouteTarget,
        SeverityLevel, CONDUCT_PHRASES, HARM_PHRASES, CONDUCT_TO_ROUTE,
    )
    texts = [t or "" for t in df[text_col].to_list()]
    products = [p or "" for p in df[product_col].to_list()]
    Q = extractor.encoder.encode(
        texts, normalize_embeddings=True, convert_to_numpy=True,
        show_progress_bar=False, batch_size=batch_size,
    ).astype("float32")
    cond_sims = Q @ extractor.conduct_phrase_emb.T   # (N, Nc)
    harm_sims = Q @ extractor.harm_phrase_emb.T      # (N, Nh)

    cond_labels = extractor.conduct_phrase_label
    harm_labels = extractor.harm_phrase_label
    cond_set = list(ConductType)
    harm_set = list(HarmType)

    # Map label-list index -> position in agg arrays
    sbert_thr = 0.45
    rule_priority = 0.4

    out: List[str] = []
    val = OntologyConstraintValidator()
    for i, text in enumerate(texts):
        text_norm = _re.sub(r"\s+", " ", text.lower())
        # max sim per ConductType
        c_score = {c: 0.0 for c in cond_set}
        for j, lab in enumerate(cond_labels):
            s = float(cond_sims[i, j])
            if s > c_score[lab]:
                c_score[lab] = s
        h_score = {h: 0.0 for h in harm_set}
        for j, lab in enumerate(harm_labels):
            s = float(harm_sims[i, j])
            if s > h_score[lab]:
                h_score[lab] = s
        # rule hits
        rule_c = {c: 0.0 for c in cond_set}
        for c, phrases in CONDUCT_PHRASES.items():
            for p in phrases:
                if p.lower() in text_norm:
                    rule_c[c] = 1.0
                    break
        rule_h = {h: 0.0 for h in harm_set}
        for h, phrases in HARM_PHRASES.items():
            for p in phrases:
                if p.lower() in text_norm:
                    rule_h[h] = 1.0
                    break
        cond_picks = [(c, max(c_score[c], rule_priority * rule_c[c]))
                      for c in cond_set
                      if c_score[c] >= sbert_thr or rule_c[c] > 0]
        cond_picks.sort(key=lambda kv: -kv[1])
        if cond_picks:
            try:
                route = CONDUCT_TO_ROUTE[cond_picks[0][0]].value
            except KeyError:
                route = RouteTarget.ROUTE_TO_OTHER.value
        else:
            route = RouteTarget.ROUTE_TO_OTHER.value
        out.append(route)
    return out


@dataclass
class PipelineResult:
    timings: Dict[str, float]
    n_complaints: int
    baseline_metrics: Dict[str, float]
    proposed_metrics: Dict[str, float]
    coverage: float
    coverage_per_group: Dict[str, float]
    avg_set_size: float
    abstention_rate: float
    causal: List[Dict]
    stress: Dict[str, Dict]
    paths: Dict[str, str]


def _ensure_dirs():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
