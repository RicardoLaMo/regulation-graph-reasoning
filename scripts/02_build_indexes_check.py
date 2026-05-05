"""Smoke-test the HybridSearcher against the 51-section regulation corpus."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from regreason.retrieve import build_default_searcher


def main():
    t0 = time.time()
    s = build_default_searcher()
    fixtures = [
        "Someone used my debit card to make unauthorized transactions and the bank wont reimburse me",
        "The mortgage servicer misapplied my escrow payment and now im being foreclosed on",
        "Debt collector keeps calling me at work and threatening lawsuits",
        "My credit report has wrong accounts and the bureau wont fix them",
        "I deposited money into a crypto wallet and the exchange froze my funds",
    ]
    for q in fixtures:
        results = s.search(q, top_k=3)
        print(f"\n>>> {q[:80]}")
        for r in results:
            print(f"   {r.passage_id} ({r.score:.3f}) {r.citation}: {r.title[:60]}")
    print(f"\nelapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
