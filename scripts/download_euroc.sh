#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/.."
# Run after explicitly authorizing the ~0.88 GB V2_01_easy download.
/usr/bin/python3 tools/download_euroc.py --download 2>&1 | tee logs/euroc_download.log
