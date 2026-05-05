# regulation-graph-reasoning

![Tests](https://github.com/RicardoLaMo/regulation-graph-reasoning/workflows/Test%20Generated%20Code/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A research-grade pipeline that runs **structured extraction + causal reasoning + conformal calibration + hypergraph-based manifold grounding** over a sample of CFPB consumer complaints, with citations to the relevant CFPB regulations.

It was built to answer four interlocking questions on every complaint:
1. **What happened?** — extract a structured `AnswerObject` (conducts, harms, severity, route, evidence spans).
2. **What does it imply causally?** — a structural causal model (DAG) over `(Product → Issue → Conduct → Harm → Severity → Route)` with `EvidenceGroundedness` as the do-intervenable treatment.
3. **How sure are we?** — Mondrian split-conformal prediction sets + temperature-scaled probabilities + a learned reject option.
4. **Why this answer?** — grounded explanations citing both complaint substrings AND CFPB regulation sections (12 CFR Reg E/Z/X/B, FCRA, FDCPA, UDAAP, etc.).

## Quickstart

```bash
# 1. environment (conda env `causalrag` works out of the box; see requirements.txt)
pip install -r requirements.txt

# 2. data symlinks (CFPB consumer complaints + 51-section compliance corpus)
ls data/   # already linked in this checkout

# 3. run end-to-end (5,000 complaints, ~10 minutes on a single GPU)
python scripts/01_bootstrap_data.py
python scripts/03_build_baseline.py             # TF-IDF + LR baseline
python scripts/04_extract_answer_objects.py     # rule + SBERT extraction + grounding
python scripts/05_fit_calibration_conformal.py  # Mondrian split-APS conformal sets
python scripts/06_run_causal_experiments.py     # do-interventions E1-E4
python scripts/07_build_hypergraph_manifold.py  # GAT over complaint↔reg hypergraph + UMAP
python scripts/08_run_stress_tests.py           # ambiguous / conflicting / adversarial
python scripts/09_render_figures.py             # LaTeX tables + remaining figs
python scripts/10_compile_report.py             # latexmk -> doc/report.pdf
```

`pytest tests/` runs the unit tests (`-m 'not slow'` to skip SBERT-loading tests).

## Repository layout

```
src/regreason/        # library
  ontology.py             AnswerObject schema + 11 ConductTypes + validator
  io_loaders.py           stratified complaint sampler + reg loader
  retrieve.py             BM25 + FAISS hybrid searcher
  extract.py              regex + SBERT canonical-phrase extractor
  grounding.py            complaint-span attribution + citation faithfulness
  baseline.py             TF-IDF + LogReg + CalibratedClassifierCV
  calibrate.py            TemperatureScaler + Platt + AbstentionPolicy
  conformal.py            MondrianAPSConformal split-conformal sets
  causal/{dag,estimands,synthetic}.py
  hypergraph_manifold/{incidence,encoder,manifold}.py
  stress/{ambiguous,conflicting,adversarial}.py
  eval/{metrics,report_tables}.py
  pipeline.py             orchestration helpers
scripts/                 numbered end-to-end pipeline (01..10)
notebooks/demo.ipynb     end-to-end narrative
tests/                   ~30 unit tests
doc/report.tex           publishable LaTeX report (built by 10_compile_report.py)
```

## Method (one-paragraph version)

We sample 5,000 CFPB consumer complaints stratified by `(Product × year)` from the post-2023 split, embed each narrative with SBERT (`all-MiniLM-L6-v2`), and run a deterministic regex-plus-SBERT extractor that emits a typed `AnswerObject` per complaint. Each `AnswerObject` is grounded by a hybrid BM25+FAISS retrieval over a 51-section CFPB regulation corpus (Reg E/Z/X/B, FCRA, FDCPA, UDAAP), producing per-conduct complaint-span citations and per-passage regulation citations. We calibrate a TF-IDF + Logistic-Regression baseline via temperature scaling and wrap it with Mondrian split-conformal prediction sets (Adaptive Prediction Sets, APS) at α=0.1 with `Product` as the conditioning group, plus a learned reject option. A networkx structural causal model encodes the assumed routing process; `EvidenceGroundedness` is the treatment of interest, and we run four do-interventions (E1–E4) with backdoor adjustment over `(Product, Issue, Conduct)` and three refutation tests (`random_common_cause`, `placebo_treatment`, `data_subset`). Finally, we build a complaint↔regulation incidence hypergraph (one hyperedge per non-empty `(Conduct, Route)` pair) and project the GAT-encoded node embeddings to 2-D with UMAP for the manifold visualization.

## Stress tests

We probe three failure modes:
- **ambiguous** narratives (concatenate first half of one product with second half of another),
- **conflicting evidence** (force a wrong product label while leaving the narrative intact),
- **adversarial** prompts (prompt injection, hallucinated citations, paraphrase, negation flip).

Metrics: abstention rate, conformal set-size growth, accuracy-given-not-abstained, citation-faithfulness rate.

## License

MIT.
