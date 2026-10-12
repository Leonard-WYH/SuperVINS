#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
g++ -std=c++17 -O2 tools/cpp_smoke.cpp -Isrc/SuperVINS/supervins_estimator/src/featureTracker -Isrc/SuperVINS/camera_models/include -I/usr/include/eigen3 -I"$SUPERVINS_ROS_PREFIX/include" -I"$ONNXRUNTIME_ROOTDIR/include" $(pkg-config --cflags opencv4) -Ldevel/lib -lsupervins_lib -L"$ONNXRUNTIME_ROOTDIR/lib" -lonnxruntime $(pkg-config --libs opencv4) -o tools/cpp_smoke
weights="$SUPERVINS_WS/src/SuperVINS/supervins_estimator/weights_dpl"
tools/cpp_smoke "$weights/superpoint.onnx" "$weights/superpoint_lightglue_fused.onnx" "$SUPERVINS_WS/results/smoke_input.png" "$SUPERVINS_WS/results/cpp" 2>&1 | tee logs/cpp_smoke.log
