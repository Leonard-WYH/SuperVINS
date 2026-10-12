#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
args=(-DCMAKE_BUILD_TYPE=Release "-DONNXRUNTIME_ROOTDIR=$ONNXRUNTIME_ROOTDIR" "-DPYTHON_EXECUTABLE=${ROS_PYTHON:-/usr/bin/python3}")
if [[ -n "${Ceres_DIR:-}" ]]; then args+=("-DCeres_DIR=$(supervins_path "$Ceres_DIR")"); fi
catkin_make "${args[@]}" "$@" -j"${BUILD_JOBS:-8}" 2>&1 | tee logs/catkin_make.log
