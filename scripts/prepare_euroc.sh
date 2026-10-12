#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
/usr/bin/python3 tools/prepare_euroc.py "$@" 2>&1 | tee logs/prepare_euroc.log
rosbag info data/V2_01_easy.bag | tee logs/rosbag_info.txt
