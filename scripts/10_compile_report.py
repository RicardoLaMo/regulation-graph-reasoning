"""Phase F-2: compile the LaTeX report via latexmk."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regreason.config import DOC


def main():
    if shutil.which("latexmk") is None:
        print("latexmk NOT FOUND. Falling back to pdflatex (if available).")
        if shutil.which("pdflatex") is None:
            print("ERROR: neither latexmk nor pdflatex is on PATH.")
            sys.exit(2)
        for _ in range(2):
            subprocess.check_call(["pdflatex", "-interaction=nonstopmode", "report.tex"], cwd=DOC)
    else:
        subprocess.check_call(["latexmk", "-pdf", "-interaction=nonstopmode", "report.tex"], cwd=DOC)
    print(f"report.pdf -> {DOC / 'report.pdf'}")


if __name__ == "__main__":
    main()
