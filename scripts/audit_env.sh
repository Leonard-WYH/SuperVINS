#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
{
 date -Is
 cat /etc/os-release
 uname -a
 nvidia-smi
 nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
 nvcc --version
 cmake --version
 g++ --version
 rosversion -d
 rosversion roscpp
 pkg-config --modversion opencv4 eigen3
 dpkg-query -W -f='${Package} ${Version}\n' libopencv-dev libeigen3-dev ros-noetic-catkin libcudnn9-cuda-12 2>/dev/null || true
 ldd "$ONNXRUNTIME_ROOTDIR/lib/libonnxruntime_providers_cuda.so"
} 2>&1 | tee logs/environment.txt
