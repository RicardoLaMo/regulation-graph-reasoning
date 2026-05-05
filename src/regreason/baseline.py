"""Baseline classifier: TF-IDF + LogReg with Platt-style calibration.

Two heads:
  - route_clf  : multiclass route prediction
  - product_clf: optional, multiclass product (used by stress-test eval)

Trains on `train.parquet` using silver labels derived from the rule-based
extractor (so the baseline competes on the same task we evaluate; this is a
deliberately weak baseline lacking causal scoring, conformal, or grounded
citations).
"""
from __future__ import annotations

import joblib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import polars as pl
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class BaselineModel:
    pipeline: Pipeline
    classes_: List[str]


def build_pipeline() -> Pipeline:
    vec = TfidfVectorizer(
        ngram_range=(1, 2), min_df=5, max_features=50_000,
        sublinear_tf=True, strip_accents="unicode",
    )
    base = LogisticRegression(
        C=1.0, max_iter=1000, class_weight="balanced", solver="lbfgs",
        multi_class="auto",
    )
    clf = CalibratedClassifierCV(base, method="sigmoid", cv=5)
    return Pipeline([("tfidf", vec), ("clf", clf)])


def train_route_baseline(
    texts: List[str], routes: List[str],
) -> BaselineModel:
    pipe = build_pipeline()
    pipe.fit(texts, routes)
    classes = list(pipe.named_steps["clf"].classes_)
    return BaselineModel(pipeline=pipe, classes_=classes)


def predict_proba(model: BaselineModel, texts: List[str]) -> np.ndarray:
    return model.pipeline.predict_proba(texts)


def predict(model: BaselineModel, texts: List[str]) -> List[str]:
    probs = predict_proba(model, texts)
    idx = probs.argmax(axis=1)
    return [model.classes_[int(i)] for i in idx]


def fit_topic_diagnostic(
    texts: List[str], n_topics: int = 20,
) -> Tuple[LatentDirichletAllocation, TfidfVectorizer, List[List[str]]]:
    """Returns (model, vectorizer, top-words-per-topic). Diagnostic only."""
    vec = TfidfVectorizer(
        ngram_range=(1, 1), min_df=10, max_features=20_000,
        stop_words="english", sublinear_tf=False,
    )
    X = vec.fit_transform(texts)
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=0,
                                    learning_method="online", max_iter=10)
    lda.fit(X)
    feature_names = vec.get_feature_names_out()
    topics: List[List[str]] = []
    for k in range(n_topics):
        top = lda.components_[k].argsort()[::-1][:15]
        topics.append([feature_names[i] for i in top])
    return lda, vec, topics


def save(model: BaselineModel, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load(path: Path) -> BaselineModel:
    return joblib.load(path)
