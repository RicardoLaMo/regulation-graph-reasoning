#!/usr/bin/env bash
# Download a CFPB complaints sample directly from the public Consumer Complaint
# Database. Removes the dependency on local symlinks under /home/wliu23.
#
# Source: https://www.consumerfinance.gov/data-research/consumer-complaints/
# API:    https://cfpb.github.io/api/ccdb/
#
# Output:
#   data/raw/complaints_sample.csv  -- 50k recent rows with narratives
#   data/compliance/cfpb_regulations.json must be supplied separately;
#   the upstream curated 51-section corpus is committed under doc/audit if
#   redistribution permits, otherwise see references in doc/references.bib.
set -euo pipefail

DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../data" && pwd)"
RAW_DIR="${DATA_DIR}/raw"
mkdir -p "${RAW_DIR}"

DATE_FROM="${DATE_FROM:-2023-03-21}"
SIZE="${SIZE:-50000}"
OUT="${RAW_DIR}/complaints_sample.csv"

URL="https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/?date_received_min=${DATE_FROM}&has_narrative=true&size=${SIZE}&format=csv"

echo "downloading ${SIZE} CFPB complaints since ${DATE_FROM} ..."
curl --fail --location --output "${OUT}" "${URL}"
echo "wrote ${OUT}"
echo
echo "Next: convert to parquet shards under data/processed/recent3y/"
echo "      see scripts/01_bootstrap_data.py for stratified sampling."
