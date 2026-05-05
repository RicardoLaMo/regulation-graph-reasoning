"""Span attribution + citation packaging.

Given a complaint text and a populated AnswerObject, attach:
  - one EvidenceSpan per top conduct (best 80-char window in the complaint)
  - one EvidenceSpan per top reg passage (from HybridSearcher)
Citation faithfulness check: does retrieved passage actually contain a keyword
related to the chosen conduct?
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import List, Optional

import numpy as np

from .ontology import AnswerObject, EvidenceSpan, ConductType, CONDUCT_PHRASES
from .retrieve import HybridSearcher


_WHITESPACE = re.compile(r"\s+")


def _windows(text: str, win: int = 80, stride: int = 40) -> List[tuple]:
    if not text:
        return []
    out = []
    for s in range(0, max(1, len(text) - win + 1), stride):
        out.append((s, min(len(text), s + win), text[s:s + win]))
    if not out:
        out.append((0, len(text), text))
    return out


def attribute(
    text: str,
    answer: AnswerObject,
    searcher: HybridSearcher,
    encoder=None,
    top_k_passages: int = 3,
) -> AnswerObject:
    spans: List[EvidenceSpan] = []
    text = text or ""

    # 1. Best complaint substring per top conduct via canonical-phrase keyword match
    if encoder is None:
        encoder = searcher.encoder
    if encoder is None:
        from sentence_transformers import SentenceTransformer
        from .config import CFG
        encoder = SentenceTransformer(CFG.sbert_model, device=CFG.device)

    for cstr in answer.conducts[:2]:
        try:
            ckey = ConductType(cstr)
        except ValueError:
            continue
        phrases = CONDUCT_PHRASES.get(ckey, [])
        best = None
        text_lower = text.lower()
        for p in phrases:
            i = text_lower.find(p.lower())
            if i >= 0:
                best = (i, i + len(p), text[i:i + len(p)], 1.0)
                break
        if best is None and phrases:
            wins = _windows(text)
            if wins:
                texts = [w[2] for w in wins]
                we = encoder.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
                pe = encoder.encode(phrases, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
                sims = we @ pe.T  # (W, P)
                idx = int(np.argmax(sims.max(axis=1)))
                score = float(sims.max())
                s, e, t = wins[idx]
                best = (s, e, t, score)
        if best is not None:
            s, e, t, sc = best
            spans.append(EvidenceSpan(
                passage_id=f"{answer.complaint_id}:{s}-{e}",
                char_start=s, char_end=e, score=float(sc),
                source="complaint", text=t,
            ))

    # 2. Top-k regulation passages
    retrieved = searcher.search(text or "(empty)", top_k=top_k_passages)
    passage_ids: List[str] = []
    for r in retrieved:
        passage_ids.append(r.passage_id)
        spans.append(EvidenceSpan(
            passage_id=r.passage_id,
            char_start=0, char_end=len(r.text),
            score=float(r.score),
            source="regulation",
            text=f"{r.citation}: {r.title}",
        ))

    out = replace(answer)
    out.evidence_spans = spans
    out.retrieved_passage_ids = passage_ids
    return out


def citation_faithful(passage_text: str, conduct: str) -> bool:
    """Cheap-and-truthful: passage must mention at least one canonical phrase
    associated with the claimed conduct."""
    try:
        c = ConductType(conduct)
    except ValueError:
        return False
    pl = (passage_text or "").lower()
    for p in CONDUCT_PHRASES.get(c, []):
        if p.lower() in pl:
            return True
    # Fallback: word overlap of conduct name itself
    return c.value.replace("_", " ") in pl
