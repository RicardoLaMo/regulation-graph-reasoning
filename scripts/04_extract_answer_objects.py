"""Phase B-2: extract AnswerObjects + ground citations on the 5k sample.

Output: artifacts/answers.parquet with columns:
  complaint_id, product, issue, conducts (list[str]), harms (list[str]),
  severity (int), route (str), confidence (float), escalation_flag (bool),
  retrieved_passage_ids (list[str]), n_complaint_spans (int), n_reg_spans (int),
  citation_faithful_rate (float).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import polars as pl
from tqdm import tqdm

from regreason.config import CFG, ARTIFACTS
from regreason.extract import build_extractor, extract_answer_object
from regreason.grounding import attribute, citation_faithful
from regreason.io_loaders import load_regulations
from regreason.retrieve import HybridSearcher


def main():
    sample_path = ARTIFACTS / "sample.parquet"
    df = pl.read_parquet(sample_path)
    print(f"loaded sample: {df.height} rows from {sample_path}")

    print("building extractor + searcher (shared SBERT encoder)...")
    extractor = build_extractor()
    regs = load_regulations()
    searcher = HybridSearcher(regs, encoder=extractor.encoder)

    rows = []
    cid_col = "complaint_id" if "complaint_id" in df.columns else None
    for i, r in enumerate(tqdm(df.iter_rows(named=True), total=df.height, desc="extract+ground")):
        cid = str(r.get(cid_col, i) if cid_col else i)
        text = r.get("narrative", "") or ""
        ans = extract_answer_object(
            text=text,
            complaint_id=cid,
            product=str(r.get("product", "")),
            issue=str(r.get("issue", "")),
            state=extractor,
        )
        ans = attribute(text, ans, searcher)
        # citation faithfulness over reg-source spans against top conduct
        if ans.conducts and ans.evidence_spans:
            reg_spans = [s for s in ans.evidence_spans if s.source == "regulation"]
            faithful = [citation_faithful(_get_passage_text(regs, s.passage_id), ans.conducts[0]) for s in reg_spans]
            cite_rate = float(np.mean(faithful)) if faithful else 0.0
        else:
            cite_rate = 0.0
        n_complaint = sum(1 for s in ans.evidence_spans if s.source == "complaint")
        n_reg = sum(1 for s in ans.evidence_spans if s.source == "regulation")
        rows.append({
            "complaint_id": ans.complaint_id,
            "product": ans.product,
            "issue": ans.issue,
            "conducts": ans.conducts,
            "harms": ans.harms,
            "severity": int(ans.severity),
            "route": ans.route,
            "confidence": float(ans.confidence),
            "escalation_flag": bool(ans.escalation_flag),
            "retrieved_passage_ids": ans.retrieved_passage_ids,
            "n_complaint_spans": int(n_complaint),
            "n_reg_spans": int(n_reg),
            "citation_faithful_rate": cite_rate,
        })

    out_df = pl.DataFrame(rows)
    out_path = ARTIFACTS / "answers.parquet"
    out_df.write_parquet(out_path)
    print(f"\nsaved {out_df.height} answers to {out_path}")
    print(f"route counts:\n{out_df['route'].value_counts()}")
    pct_with_conduct = float((out_df['conducts'].list.len() > 0).mean())
    print(f"complaints with >=1 conduct: {pct_with_conduct:.3f}")


def _get_passage_text(regs, pid: str) -> str:
    for r in regs:
        if r.section_id == pid:
            return r.text
    return ""


if __name__ == "__main__":
    main()
