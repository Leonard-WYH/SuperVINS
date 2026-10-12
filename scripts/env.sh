#!/usr/bin/env bash
# Source this file only in a dedicated SuperVINS shell.
SUPERVINS_WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
unset CMAKE_PREFIX_PATH ROS_PACKAGE_PATH ROSLISP_PACKAGE_DIRECTORIES
source /opt/ros/noetic/setup.bash
export ONNXRUNTIME_ROOTDIR="$SUPERVINS_WS/deps/onnxruntime-1.23.2"
export LD_LIBRARY_PATH="$ONNXRUNTIME_ROOTDIR/lib:/usr/local/cuda-12.8/lib64:/opt/ros/noetic/lib"
export ROS_MASTER_URI="${SUPERVINS_MASTER_URI:-http://127.0.0.1:11321}"
export ROS_IP=127.0.0.1
export ROS_HOME="$SUPERVINS_WS/logs/ros"
if [[ -f "$SUPERVINS_WS/devel/setup.bash" ]]; then source "$SUPERVINS_WS/devel/setup.bash"; fi
