#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
catkin_make -DCMAKE_BUILD_TYPE=Release -DONNXRUNTIME_ROOTDIR="$ONNXRUNTIME_ROOTDIR" -DCeres_DIR=/usr/local/lib/cmake/Ceres -DPYTHON_EXECUTABLE=/usr/bin/python3 -j8 2>&1 | tee logs/catkin_make.log
