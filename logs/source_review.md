# Source/configuration audit

Reviewed official README and Dockerfile, all three package manifests/CMake files, all EuRoC YAMLs, the camera model factory/calibration and projection implementations, estimator parameter loading/main input synchronization, frontend extraction/matching/preprocessing/tracking, IMU integration/initialization/nonlinear optimization, visualization/TUM writing, loop descriptor transport, keyframe PnP verification, DBoW3 vocabulary/database interfaces, 4DoF/6DoF pose-graph solving and RViz configuration.

Concrete findings verified during execution:

- The released models are present and pass ONNX checks. The expected SuperPoint DBoW3 vocabulary is absent; an ORB vocabulary is not a valid substitute for CV_32F 256-dimensional descriptors.
- The original estimator includes bundled ORT API 15 headers while loop matcher includes SDK headers. Both now use the same ORT 1.23.2 SDK.
- Hardcoded /opt/onnxruntime and author-specific Ceres search paths prevent a portable dependency selection. A cache SDK root and the actual installed Ceres configuration fix discovery/linking.
- Monocular original match threshold 1.0 is inconsistent with the strict score > threshold filter. Local runtime threshold is 0.5.
- The original stereo/UMAVI YAMLs contain author-specific output and model paths; the UMAVI camera calibration file is absent. They were not used for this experiment. Main CMake source root is the Catkin src directory, so model/vocabulary relative paths include SuperVINS/.
- Estimator output path is used as supplied; loop originally prepends src to even absolute output paths. Absolute loop output/save paths are now respected.
- Original mono settings enable camera/IMU extrinsics and camera/IMU time-offset estimation. The first full replay diverged. Dataset camera calibration plus fixed known extrinsics/td produced successful complete replays. This does not isolate which individual change caused the divergence.
- Official IMU tuning is retained (acc_n=0.1, gyr_n=0.01, acc_w=0.001, gyr_w=0.0001), which differs from EuRoC sensor.yaml noise densities. These are recorded rather than silently treated as identical units/model parameters.
- Frontend tracks all 20 Hz images, but multiple_thread inserts only every second feature frame into the estimator: nominal odometry is 10 Hz. The YAML freq setting does not override this hardcoded subsampling.
- The extractor resizes maximum image edge to 512, so EuRoC 752x480 becomes 512x327. Frontend LightGlue normalizes scaled feature coordinates using source image dimensions; this existing behavior was preserved and successful replay verified.
- CUDA EP uses GPU convolution fallback algorithms on this GPU with the original DEFAULT cuDNN search. CUDA kernel profiles prove that this message does not mean CPU EP fallback.
- Dense loop_corrected_tum.txt rebuilds all raw VIO poses with one latest rigid drift transform. SE(3)-aligned ATE is therefore equal to raw VIO ATE. The nonrigid pose-graph result is the sparse keyframe path/vio_loop.csv. These are evaluated separately.
- Pose-graph Ceres iteration limit is 5. NO_CONVERGENCE at the iteration limit can still have reduced cost; reports are retained and do not establish a globally converged optimum.
- failureDetection() immediately returns false in upstream code. Automated finite-output, timestamp, quaternion, loop-acceptance and correction checks are therefore performed externally. This core behavior was not removed or rewritten.
- Legacy BRIEF is still computed in keyframe constructors; observed accepted closures explicitly report LightGlue, so BRIEF fallback is not misreported as the requested loop verification.
- Dormant #if 0 debug image paths and usage examples refer to /home/tony-ws1. They do not execute in the selected configuration.
- Relative time_consumption logs require an existing directory; each replay now gets its own run directory and timing subdirectory.
