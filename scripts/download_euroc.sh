#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/common.sh"
cd "$SUPERVINS_WS"
/usr/bin/python3 tools/download_euroc.py --download 2>&1 | tee logs/euroc_download.log
