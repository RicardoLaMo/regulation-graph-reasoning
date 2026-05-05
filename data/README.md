# `data/` — symlinks to local CFPB assets (not committed)

This project consumes three external data sources, all of which are
referenced via symlinks under this directory and excluded from version
control via `.gitignore`:

| Symlink | Points to | Description |
| --- | --- | --- |
| `data/recent3y/` | `cfpb/data/processed/recent3y/` | CFPB consumer-complaint splits filtered to dates ≥ 2023-03-21. Files: `train.parquet` (372k rows), `val.parquet` (339k), `test.parquet` (1.6M), `calibration.parquet` (~6k). Schema: `complaint_id, date_received, product, sub_product, issue, sub_issue, narrative`. |
| `data/compliance/` | `data/compliance/` | Curated 51-section CFPB regulatory corpus (Reg E/Z/X/B, FCRA, FDCPA, UDAAP, FinTech / crypto). File: `cfpb_regulations.json`. Schema: `id, regulation, citation, title, route_tags, conduct_tags, text`. |
| `data/compliance_indexes/` | `cfpb/artifacts/compliance/` | Pre-built dual-index (`faiss_index.pkl`, `bm25_index.pkl`) over the 51 sections, plus `passage_store.json` and `index_meta.json`. Encoder: `sentence-transformers/all-MiniLM-L6-v2` (384-dim). |

The runtime `HybridSearcher` rebuilds its FAISS index in-memory on first use
(typically < 6 s for 51 passages on a single GPU), so the pickled
indexes are convenient but not strictly required.

## Reproducing the symlinks

```bash
ln -s /path/to/cfpb/data/processed/recent3y         data/recent3y
ln -s /path/to/data/compliance                      data/compliance
ln -s /path/to/cfpb/artifacts/compliance            data/compliance_indexes
```
