"""Render LaTeX tables (booktabs) into doc/tables/*.tex from pandas DataFrames."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def write_table(df: pd.DataFrame, out_path: Path, *, caption: Optional[str] = None,
                label: Optional[str] = None, float_format: str = "%.3f",
                index: bool = False, wide: bool = False) -> Path:
    """Render a DataFrame as a booktabs LaTeX table.

    `wide=True` wraps the tabular in `\\resizebox{\\textwidth}{!}{...}` so wide
    tables shrink to the text width instead of overflowing the right margin.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = df.to_latex(
        index=index,
        escape=True,
        float_format=float_format,
        column_format="l" + "c" * (len(df.columns) - (0 if index else 0)),
        na_rep="--",
    ).strip()
    parts = [r"\begin{table}[htbp]", r"\centering", r"\small"]
    if wide:
        parts.append(r"\resizebox{\textwidth}{!}{%")
        parts.append(body)
        parts.append(r"}")
    else:
        parts.append(body)
    if caption:
        parts.append(r"\caption{" + caption + "}")
    if label:
        parts.append(r"\label{" + label + "}")
    parts.append(r"\end{table}")
    out_path.write_text("\n".join(parts) + "\n")
    return out_path
