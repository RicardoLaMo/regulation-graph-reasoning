"""Hybrid BM25+FAISS searcher over the CFPB regulation corpus."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from .config import CFG, COMPLIANCE_INDEXES
from .io_loaders import load_prebuilt_indexes, load_regulations, RegSection


_TOKENIZE = re.compile(r"[a-z0-9]+")


def _tokenize(s: str) -> List[str]:
    return _TOKENIZE.findall(s.lower())


@dataclass
class Retrieved:
    passage_id: str
    score: float
    text: str
    citation: str
    title: str


class HybridSearcher:
    """BM25 + dense FAISS, alpha-blended on min-max-normalized scores."""

    def __init__(self, regs: List[RegSection], encoder=None, alpha: float = CFG.bm25_alpha):
        from rank_bm25 import BM25Okapi
        self.regs = regs
        self.alpha = alpha
        self.tokens = [_tokenize(r.title + " " + r.text) for r in regs]
        self.bm25 = BM25Okapi(self.tokens)
        self.passage_ids = [r.section_id for r in regs]
        self._embeddings: Optional[np.ndarray] = None
        self._faiss = None
        self.encoder = encoder

    def _ensure_dense(self):
        if self._faiss is not None:
            return
        if self.encoder is None:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(CFG.sbert_model, device=CFG.device)
        texts = [r.title + ". " + r.text for r in self.regs]
        emb = self.encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        self._embeddings = emb.astype("float32")
        import faiss
        d = self._embeddings.shape[1]
        self._faiss = faiss.IndexFlatIP(d)
        self._faiss.add(self._embeddings)

    @staticmethod
    def _minmax(scores: np.ndarray) -> np.ndarray:
        if scores.size == 0:
            return scores
        s = scores.astype(np.float64)
        lo, hi = float(s.min()), float(s.max())
        if hi - lo < 1e-9:
            return np.zeros_like(s)
        return (s - lo) / (hi - lo)

    def search(self, query: str, top_k: int = CFG.top_k_retrieval) -> List[Retrieved]:
        self._ensure_dense()
        bm25_scores = np.array(self.bm25.get_scores(_tokenize(query)), dtype=np.float64)
        q_emb = self.encoder.encode([query], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False).astype("float32")
        D, I = self._faiss.search(q_emb, len(self.regs))
        dense_scores = np.zeros(len(self.regs), dtype=np.float64)
        for rank, idx in enumerate(I[0]):
            dense_scores[int(idx)] = float(D[0][rank])

        bm25_n = self._minmax(bm25_scores)
        dense_n = self._minmax(dense_scores)
        blended = self.alpha * bm25_n + (1 - self.alpha) * dense_n
        order = np.argsort(-blended)[:top_k]
        out: List[Retrieved] = []
        for i in order:
            r = self.regs[int(i)]
            out.append(Retrieved(
                passage_id=r.section_id,
                score=float(blended[int(i)]),
                text=r.text,
                citation=r.citation,
                title=r.title,
            ))
        return out

    def embed_corpus(self) -> np.ndarray:
        self._ensure_dense()
        return self._embeddings


def build_default_searcher(encoder=None) -> HybridSearcher:
    regs = load_regulations()
    return HybridSearcher(regs, encoder=encoder)
