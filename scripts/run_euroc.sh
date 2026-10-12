#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
/usr/bin/python3 tools/run_euroc.py "$@"
