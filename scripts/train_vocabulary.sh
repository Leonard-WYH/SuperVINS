#!/usr/bin/env bash
set -eo pipefail
source "$(dirname "$0")/env.sh"
cd "$SUPERVINS_WS"
dbow="src/SuperVINS/supervins_loop_fusion/src/ThirdParty/DBoW3/src"
g++ -std=c++17 -O2 tools/train_vocabulary.cpp "$dbow"/*.cpp "$dbow/quicklz.c" -I"$dbow" -Isrc/SuperVINS/supervins_estimator/src/featureTracker -I/opt/ros/noetic/include -I/usr/include/eigen3 -Isrc/SuperVINS/camera_models/include -I"$ONNXRUNTIME_ROOTDIR/include" $(pkg-config --cflags opencv4) -Ldevel/lib -lsupervins_lib -L"$ONNXRUNTIME_ROOTDIR/lib" -lonnxruntime $(pkg-config --libs opencv4) -o tools/train_vocabulary
out="src/SuperVINS/supervins_loop_fusion/src/ThirdParty/Voc/superpoint1.yml.gz"
if [[ -e "$out" ]]; then echo "Vocabulary exists: $out; refusing to overwrite."; exit 1; fi
tools/train_vocabulary src/SuperVINS/supervins_estimator/weights_dpl/superpoint.onnx 'data/vocabulary_training/*.png' "$out" 2>&1 | tee logs/vocabulary_training.log
