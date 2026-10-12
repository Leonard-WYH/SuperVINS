#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/.."
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
 rg '^#define CERES_VERSION_(MAJOR|MINOR|REVISION)' /usr/local/include/ceres/version.h
 rg '^#define CUDNN_(MAJOR|MINOR|PATCHLEVEL)' /usr/include/x86_64-linux-gnu/cudnn_version.h
 dpkg-query -W -f='${Package} ${Version}\n' libopencv-dev libeigen3-dev ros-noetic-catkin libcudnn9-cuda-12
 git -C src/SuperVINS log -1 --format=fuller
 ldd deps/onnxruntime-1.23.2/lib/libonnxruntime_providers_cuda.so
 /usr/bin/python3 -m pip show onnxruntime-gpu
 /home/wyh/anaconda3/envs/neo/bin/python -c 'import onnxruntime; print(onnxruntime.__version__, onnxruntime.get_available_providers())'
} 2>&1 | tee logs/environment.txt
