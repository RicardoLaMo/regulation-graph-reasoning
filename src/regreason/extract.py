"""Hybrid extractor: regex/keyword + SBERT canonical-phrase similarity → AnswerObject."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import CFG
from .ontology import (
    AnswerObject,
    ConductType,
    HarmType,
    OntologyConstraintValidator,
    RouteTarget,
    SeverityLevel,
    conduct_canonical_phrases,
    harm_canonical_phrases,
    CONDUCT_TO_ROUTE,
    CONDUCT_PHRASES,
    HARM_PHRASES,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _has_phrase(text_norm: str, phrase: str) -> bool:
    return phrase.lower() in text_norm


@dataclass
class ExtractorState:
    encoder: object
    conduct_phrase_emb: np.ndarray         # (Nc, d)
    conduct_phrase_label: List[ConductType]
    harm_phrase_emb: np.ndarray            # (Nh, d)
    harm_phrase_label: List[HarmType]


def build_extractor(encoder=None) -> ExtractorState:
    from sentence_transformers import SentenceTransformer
    if encoder is None:
        encoder = SentenceTransformer(CFG.sbert_model, device=CFG.device)
    cphr = conduct_canonical_phrases()
    hphr = harm_canonical_phrases()
    cemb = encoder.encode([p for _, p in cphr], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    hemb = encoder.encode([p for _, p in hphr], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return ExtractorState(
        encoder=encoder,
        conduct_phrase_emb=cemb.astype("float32"),
        conduct_phrase_label=[c for c, _ in cphr],
        harm_phrase_emb=hemb.astype("float32"),
        harm_phrase_label=[h for h, _ in hphr],
    )


def _severity_from_signals(text_norm: str, harms: List[HarmType]) -> int:
    sev = SeverityLevel.LOW.value
    if any(k in text_norm for k in ["thousands of dollars", "$1000", "$5000", "life savings", "took everything", "wiped out"]):
        sev = max(sev, SeverityLevel.URGENT.value)
    if any(k in text_norm for k in ["foreclos", "evict", "homeless", "bankruptcy"]):
        sev = max(sev, SeverityLevel.CRITICAL.value)
    if HarmType.MONETARY_LOSS in harms:
        sev = max(sev, SeverityLevel.MEDIUM.value)
    if HarmType.CREDIT_DAMAGE in harms or HarmType.DENIAL_OF_SERVICE in harms:
        sev = max(sev, SeverityLevel.HIGH.value)
    if HarmType.DISCRIMINATION_HARM in harms or HarmType.PRIVACY_VIOLATION in harms:
        sev = max(sev, SeverityLevel.URGENT.value)
    return int(sev)


def _aggregate_phrase_scores(emb_q: np.ndarray, emb_phr: np.ndarray, labels) -> Dict[object, float]:
    """For each label, return max cosine sim across that label's canonical phrases."""
    sims = (emb_q @ emb_phr.T).reshape(-1)  # (Nphr,)
    out: Dict[object, float] = {}
    for s, lab in zip(sims.tolist(), labels):
        if s > out.get(lab, -1.0):
            out[lab] = float(s)
    return out


def extract_answer_object(
    text: str,
    complaint_id: str,
    product: str,
    issue: str,
    state: ExtractorState,
    *,
    sbert_threshold: float = 0.45,
    rule_priority: float = 0.4,
) -> AnswerObject:
    text_norm = _norm(text)
    q_emb = state.encoder.encode([text or ""], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype("float32")
    cond_scores = _aggregate_phrase_scores(q_emb, state.conduct_phrase_emb, state.conduct_phrase_label)
    harm_scores = _aggregate_phrase_scores(q_emb, state.harm_phrase_emb, state.harm_phrase_label)

    rule_hits_c: Dict[ConductType, float] = {}
    for c, phrases in CONDUCT_PHRASES.items():
        for p in phrases:
            if _has_phrase(text_norm, p):
                rule_hits_c[c] = max(rule_hits_c.get(c, 0.0), 1.0)
    rule_hits_h: Dict[HarmType, float] = {}
    for h, phrases in HARM_PHRASES.items():
        for p in phrases:
            if _has_phrase(text_norm, p):
                rule_hits_h[h] = max(rule_hits_h.get(h, 0.0), 1.0)

    conducts: List[Tuple[ConductType, float]] = []
    for c in ConductType:
        score = max(cond_scores.get(c, 0.0), rule_priority * rule_hits_c.get(c, 0.0))
        if score >= sbert_threshold or rule_hits_c.get(c, 0.0) > 0:
            conducts.append((c, score))
    conducts.sort(key=lambda kv: -kv[1])

    harms: List[Tuple[HarmType, float]] = []
    for h in HarmType:
        score = max(harm_scores.get(h, 0.0), rule_priority * rule_hits_h.get(h, 0.0))
        if score >= sbert_threshold or rule_hits_h.get(h, 0.0) > 0:
            harms.append((h, score))
    harms.sort(key=lambda kv: -kv[1])

    cond_labels = [c.value for c, _ in conducts[:3]]
    harm_labels = [h.value for h, _ in harms[:3]]
    severity = _severity_from_signals(text_norm, [h for h, _ in harms])

    if conducts:
        try:
            route = CONDUCT_TO_ROUTE[conducts[0][0]].value
        except KeyError:
            route = RouteTarget.ROUTE_TO_OTHER.value
    else:
        route = RouteTarget.ROUTE_TO_OTHER.value

    if conducts:
        confidence = float(min(1.0, max(c[1] for c in conducts)))
    else:
        confidence = 0.0

    ans = AnswerObject(
        complaint_id=str(complaint_id),
        product=str(product or ""),
        issue=str(issue or ""),
        conducts=cond_labels,
        harms=harm_labels,
        severity=severity,
        route=route,
        confidence=confidence,
        ood_score=float(1.0 - confidence),
        escalation_flag=(severity >= SeverityLevel.URGENT.value),
    )
    val = OntologyConstraintValidator().validate(ans)
    return val.repaired
