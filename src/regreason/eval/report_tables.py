"""Render LaTeX tables (booktabs) into doc/tables/*.tex from pandas DataFrames."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def write_table(df: pd.DataFrame, out_path: Path, *, caption: Optional[str] = None,
                label: Optional[str] = None, float_format: str = "%.3f",
                index: bool = False) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = df.to_latex(
        index=index,
        escape=True,
        float_format=float_format,
        column_format="l" + "c" * (len(df.columns) - (0 if index else 0)),
        na_rep="--",
    )
    parts = [r"\begin{table}[htbp]", r"\centering", r"\small"]
    parts.append(body.strip())
    if caption:
        parts.append(r"\caption{" + caption + "}")
    if label:
        parts.append(r"\label{" + label + "}")
    parts.append(r"\end{table}")
    out_path.write_text("\n".join(parts) + "\n")
    return out_path
