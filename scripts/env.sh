#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ROS_SETUP_FILE="$(supervins_path "${ROS_SETUP_FILE:-/opt/ros/noetic/setup.bash}")"
[[ -f "$ROS_SETUP_FILE" ]] || { echo "ROS Noetic setup missing: $ROS_SETUP_FILE" >&2; return 1; }
unset CMAKE_PREFIX_PATH ROS_PACKAGE_PATH ROSLISP_PACKAGE_DIRECTORIES
source "$ROS_SETUP_FILE"
export ONNXRUNTIME_ROOTDIR="$(supervins_path "${ONNXRUNTIME_ROOTDIR:-deps/onnxruntime-1.23.2}")"
if [[ -z "${CUDA_HOME:-}" ]] && command -v nvcc >/dev/null; then
    CUDA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v nvcc)")")")"
fi
SUPERVINS_CUDA_LIB=""
if [[ -n "${CUDA_HOME:-}" ]]; then
    CUDA_HOME="$(supervins_path "$CUDA_HOME")"
    SUPERVINS_CUDA_LIB="$CUDA_HOME/lib64"
fi
SUPERVINS_ROS_PREFIX="$(dirname "$ROS_SETUP_FILE")"
export LD_LIBRARY_PATH="$ONNXRUNTIME_ROOTDIR/lib${SUPERVINS_CUDA_LIB:+:$SUPERVINS_CUDA_LIB}:$SUPERVINS_ROS_PREFIX/lib"
export ROS_MASTER_URI="${SUPERVINS_MASTER_URI:-http://127.0.0.1:11321}"
export ROS_IP=127.0.0.1
export ROS_HOME="$SUPERVINS_WS/logs/ros"
if [[ -f "$SUPERVINS_WS/devel/setup.bash" ]]; then source "$SUPERVINS_WS/devel/setup.bash"; fi
