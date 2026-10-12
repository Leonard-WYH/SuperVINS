# SuperVINS 2.0 本机原生复现记录

日期：2026-10-12，Asia/Shanghai。工作空间：`/home/wyh/Project/Prometheus/Modules/SuperVINS`。

## 结论与交付范围

已在本机 Ubuntu 20.04 + ROS1 Noetic + C++/Catkin 上完成编译、GPU SuperPoint/LightGlue 测试，以及两轮完整 EuRoC V2_01_easy 运行、LightGlue 回环接受、4DoF 位姿图求解、RViz 显示与 EVO 评测。没有使用 Docker，没有更改系统 NVIDIA 驱动、CUDA、cuDNN、ROS，也没有修改其他项目。测试启动的 ROS 进程已退出，原有应用未被主动停止。

这次完成的是系统功能复现，**并非作者论文实验的逐项等价复现**：官方仓库没有发布所需 SuperPoint 词袋，本次使用独立于 V2_01_easy 的官方演示视频画面自训练词袋；运行配置固定了已知外参与时间偏移，并使用数据集实际相机标定。原始 VINS-Fusion 对比和 D435i 真机运行没有执行。

最终结果：[`results/latest`](results/V2_01_easy_20261012_151641)，实际目录为 `results/V2_01_easy_20261012_151641`。此前成功运行也完整保存在 `results/V2_01_easy_20261012_151208`。失败的第一轮保存在 `results/V2_01_easy_20261012_150931`，不能作为成功结果。

## 1. 环境版本与 GPU

| 项目 | 实测值 |
|---|---|
| Ubuntu / 内核 | 20.04.6 LTS / 5.15.0-139-generic |
| ROS | Noetic，roscpp 1.17.4 |
| Catkin | ros-noetic-catkin 0.8.12 |
| GPU | NVIDIA GeForce RTX 5070 Ti，计算能力 12.0，16,303 MiB |
| NVIDIA 驱动 | 580.105.08 |
| CUDA Toolkit | 12.8，nvcc V12.8.61 |
| nvidia-smi 显示的 CUDA | 13.0，是驱动支持上限，不能当作已安装 Toolkit 版本 |
| cuDNN | 9.10.2.21，头文件 9.10.2 |
| OpenCV | Ubuntu 原生 4.2.0 |
| Eigen | 3.3.7 |
| Ceres | 已有 `/usr/local` 安装的 2.1.0，静态库 |
| CMake / GCC | 3.24.4 / 9.4.0；系统另有 CMake 3.16.3，构建使用 PATH 中的 3.24.4 |
| ROS Python | `/usr/bin/python3`，3.8 |
| 模型诊断 Python | 已有 conda neo 环境 Python 3.10，仅复用，不修改该环境 |
| EVO | 1.29.0，安装于工作空间 `deps/evo-venv310` |

完整原始输出：[`logs/environment.txt`](logs/environment.txt)。检查时桌面与 AirSim 已占用 GPU；最终 GPU 整卡统计也包含背景负载。

### ONNX Runtime 兼容性

系统 Python 原有 `onnxruntime-gpu==1.16.3`。实际加载官方 SuperPoint 时 CUDA Provider 失败，缺少 `libcublasLt.so.11`，session 只剩 CPU Provider。测试明确失败，未把回退误判为 GPU 成功：[`logs/ort_1.16.3_smoke.log`](logs/ort_1.16.3_smoke.log)。`ldd` 同时发现 cuDNN 8、cuBLAS 11、cuFFT 10、CUDA Runtime 11 库缺失。

因此未安装旧 CUDA/cuDNN 来尝试强行运行 1.16.3，也没有证明“任何构建的 1.16.3 在任何 Blackwell 环境下都不可能工作”。本机官方旧版本的依赖组合不可直接使用。

选择已有 `onnxruntime-gpu 1.23.2`：从 neo 环境复制 C++ runtime、CUDA/shared provider 到 `deps/onnxruntime-1.23.2/lib`，从 Microsoft `v1.23.2` 下载配套 C/C++ 头文件。库以 `libonnxruntime.so.1` 为 SONAME；CUDA 12/cuDNN 9 依赖均能解析。两个 ROS C++ 节点和原始推理类的真实测试通过，验证了本机 GPU 和 SuperVINS 所使用的 C++ API。

检查资料：[ORT CUDA EP 官方文档](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)、[NVIDIA Blackwell 兼容指南](https://docs.nvidia.com/cuda/blackwell-compatibility-guide/index.html)、[GPU 计算能力](https://developer.nvidia.com/cuda/gpus)。结论以本机执行结果为准。

## 2. 源码与资源

官方仓库：<https://github.com/luohongk/SuperVINS>。克隆到 `src/SuperVINS`，使用浅克隆固定当前提交：

```text
e9689cf72cebbc7901b110ff201daedf27b0c3ff
作者提交日期：2026-06-24 15:58:15 +0800
```

已检查 README、三包 CMakeLists.txt/package.xml、EuRoC 配置、相机模型、前端、IMU/初始化/优化、回环/PnP/DBoW3、位姿图和输出实现。具体发现见 [`logs/source_review.md`](logs/source_review.md)；源码清单见 `logs/source_inventory.txt`。

| 必需资源 | 状态 |
|---|---|
| camera_models | 编译成功，包括 Calibrations 工具 |
| supervins_estimator，ROS 包名 supervins | 编译、GPU 模型加载、完整播放成功 |
| supervins_loop_fusion | 编译、DBoW3 检索、LightGlue+PnP、4DoF 优化成功执行 |
| weights_dpl/superpoint.onnx | 仓库自带，ONNX checker 通过，opset 17 |
| weights_dpl/superpoint_lightglue_fused.onnx | 仓库自带，ONNX checker 通过，opset 17 + com.microsoft 1 |
| src/ThirdParty/Voc/superpoint1.yml.gz | 官方缺失；本次自训练生成 |
| support_files/brief_pattern.yml | 存在；上游仍在关键帧构造中计算 BRIEF |

词袋来源：仓库 `resources/video.mp4`，3–44 秒每秒一帧，共 42 帧；裁剪相机窗口 `y=384:750, x=2:573`，转灰度并用同一个 SuperPoint GPU 模型提取 256 维浮点描述子。DBoW3 使用 k=10、L=4、TF_IDF/L1，重载后的词数为 9,523。

训练图像含原演示的特征绘制标记、场景覆盖有限；没有用 V2_01_easy 评测图像训练。它能支持本次回环功能验证，但不能代表作者的训练集、词袋或论文精度。官方关于缺失词袋的说明见 [Issue #8](https://github.com/luohongk/SuperVINS/issues/8) 与 [DBoW3 仓库](https://github.com/rmsalinas/DBow3)。不能用 ORB 词袋替代 SuperPoint 浮点描述子词袋。

资源哈希：[`logs/artifact_sha256.txt`](logs/artifact_sha256.txt)，校验结果 `logs/checksums_verified.txt`；词袋来源 `logs/vocabulary_manifest.json`，训练日志 `logs/vocabulary_training.log`。

## 3. 依赖与构建

复用已安装的 ROS/OpenCV/Eigen/Ceres/CUDA/cuDNN/Boost/glog/gflags/SuiteSparse/JPEG/PNG。DBoW3 使用上游仓库已内嵌的源码，直接编入 Loop Fusion，没有替换成另一套算法，也没有系统级安装额外 DBoW3。

新建工作空间内的 ORT SDK 和 EVO venv。EVO 完整依赖清单：`logs/evo_requirements.txt`。系统 Python 缺少 ensurepip，第一次创建 Python 3.8 venv 失败；改用已有 Python 3.10 的 venv 后成功，没有为此修改系统 Python。

工作空间根目录放置 `CATKIN_IGNORE`，防止上层 Prometheus 的 Catkin 扫描把本独立工作空间纳入其构建；本工作空间从 `src/` 扫描，仍能正常发现三个包。

```bash
cd /home/wyh/Project/Prometheus/Modules/SuperVINS
./scripts/setup_ort.sh
./scripts/build.sh
```

实际构建命令：

```bash
catkin_make -DCMAKE_BUILD_TYPE=Release \
  -DONNXRUNTIME_ROOTDIR="$PWD/deps/onnxruntime-1.23.2" \
  -DCeres_DIR=/usr/local/lib/cmake/Ceres \
  -DPYTHON_EXECUTABLE=/usr/bin/python3 -j8
```

最终日志 `logs/catkin_make.log`，初始构建及 C++17 失败日志亦保留。最终 camera_models、Calibrations、supervins_lib、supervins_node、supervins_loop_fusion_node 全部构建成功。

### 必要源码修改

补丁：[`logs/source_changes.patch`](logs/source_changes.patch)，基于上述固定提交，可审查和重放。保留全部核心算法。

1. 三个包使用已安装 Ceres 2.1，移除作者 `/home/lhk/Thirdparty/Ceres` 搜索路径。
2. 新增 `cmake/OnnxRuntime.cmake`：SDK 根目录改为 CMake CACHE PATH，通过明确的 SDK include/library 路径链接；删除硬编码 `/opt/onnxruntime`。
3. 前端改为使用选定 SDK 的 ORT 头文件，避免前端 API 15 与 Loop Fusion 新头文件混用。
4. 两个推理包使用 C++17，满足新 SDK 头文件；内嵌 DBoW3 的六处旧动态异常声明移除，实际异常抛出和算法不变。
5. Loop Fusion 尊重绝对的输出/pose graph 路径，避免把 Catkin src 前缀再次拼到绝对路径前。
6. 4DoF/6DoF 求解后增加 Ceres BriefReport 日志，用于验证实际优化和 cost。

配置修改在 `scripts/configure_euroc.py` 与工作空间 `config/`，没有覆盖作者原始 YAML。模型、词袋仍沿用相对于 Catkin `src` 的原始路径（以 `SuperVINS/` 开头）；输出使用各轮目录的绝对路径。

## 4. 神经网络真实测试

执行 Python 和 C++ 原始 Extractor_DPL/Matcher_DPL。测试使用仓库概览图，以及 V2_01_easy 第 200 张图像与水平平移 6 像素的配对图；这些是推理诊断，不是额外 SLAM 评测序列。

```bash
./scripts/test_cpp.sh
/home/wyh/anaconda3/envs/neo/bin/python tools/onnx_smoke.py \
  --input results/euroc_smoke_input.npy --report euroc_onnx_smoke
python3 tools/profile_summary.py
```

| 检查 | 实测结果 |
|---|---|
| SuperPoint/LightGlue 模型加载 | 两模型成功 |
| CUDA Provider | 成功初始化，CUDA 算子执行得到 profiling 证据 |
| C++ 概览图配对 | SuperPoint 495/504 点，LightGlue 336 对有效匹配 |
| EuRoC 图像配对 | SuperPoint 输出 542/549 个关键点及 256 维描述子，LightGlue 404 对原始匹配，其中 386 对 score > 0.5 |
| NaN/Inf | Python 检查全部原始输出通过；C++ 检查描述子/SP 浮点输出和匹配分数通过 |
| EuRoC 配对预热后延迟 | SuperPoint 约 4–7 ms；LightGlue 约 8–15 ms，具体逐次耗时保留 |
| GPU 状态 | 模型与 ROS 节点在本 GPU 上执行成功，完整数据集无 Matcher GPU inference failed |

首次 Python 概览测试的冷启动含 CUDA 内核 JIT 等开销：SP 约 32.4 s、LG 约 8.8 s；后续冷缓存已建立，不能只报预热耗时来代表首次启动。

C++ profiling 中 SuperPoint 每次约 199 个 CUDA Node 事件，LightGlue 每次约 1,200 个 CUDA Node 事件；其余 CPU 事件包括形状/控制相关算子。`results/cpp_gpu_profile_summary.json` 列出 CUDA op 类型，原始 trace 在 `results/cpp_sp_*.json`、`results/cpp_lg_*.json`。这证明不是整个模型悄悄回退到 CPU。

原 cuDNN DEFAULT 搜索在本 GPU 上打印 Conv “Fallback mode”警告，但 profiling 中 Conv 仍属于 CUDA Provider，这与 1.16.3 的 CPU-only fallback 是两种不同情况。

结果文件：`results/euroc_onnx_smoke.json`、`results/onnx_smoke.json`、`logs/cpp_smoke.log`、`logs/euroc_onnx_smoke.log`。匹配图：[`results/euroc_lightglue_matches.png`](results/euroc_lightglue_matches.png)。

## 5. EuRoC 数据与配置

经用户批准下载这一条序列。ETH 官方旧 robotics.ethz.ch 链接失效，新 Research Collection 在本机返回 HTTP 429。选择可核验的 HF 镜像并固定 revision：

```text
GlowBond/EuRoC_MAV_Dataset
29d08aeb1c8d9dc5c30497cc538d9cc61f872bb7
归档内：vicon_room2/V2_01_easy/V2_01_easy.zip
```

通过 HTTP Range 只取内层 V2_01_easy.zip，传输压缩数据 882,940,281 bytes，没有下载 6 GB 全归档。验证外层 entry CRC、解压 CRC；本地 ZIP SHA256：

```text
06875e7591a883c7bfadc4604c41dce4837a475fe272e0337650141bc9530262
```

这是镜像完整性与本地身份验证，未获得 ETH 官方独立哈希作逐字节认证。来源/偏移/CRC/哈希见 `logs/euroc_download_metadata.json`。[镜像文件](https://huggingface.co/datasets/GlowBond/EuRoC_MAV_Dataset/blob/29d08aeb1c8d9dc5c30497cc538d9cc61f872bb7/vicon_room2.zip)，[EuRoC 官方介绍](https://projects.asl.ethz.ch/datasets/euroc-mav/)。

使用 CSV/PNG 生成原生 ROS1 LZ4 bag：保持原始纳秒时间戳，保留两个相机与 IMU，图像 mono8，角速度 rad/s，加速度 m/s²；按时间排序。不是下载的原始官方 bag 字节副本。真值由 `state_groundtruth_estimate0/data.csv` 转换，重排 quaternion wxyz 为 TUM xyzw，使用 IMU/body 位姿。

| topic | 消息数 | 频率 |
|---|---:|---:|
| /cam0/image_raw | 2,280 | 20 Hz |
| /cam1/image_raw | 2,280 | 20 Hz |
| /imu0 | 22,800 | 200 Hz |

bag 时长约 113.995 s，大小约 1.4 GB。每个传感器时间戳严格递增；数量重读验证通过。原始记录 `logs/rosbag_info.txt`、`logs/euroc_data_audit.json`。

### 最终运行参数

- 单目 + IMU；image0 `/cam0/image_raw`，IMU `/imu0`，752×480。
- 相机 PINHOLE + radial-tangential，cam0 fx=458.654、fy=457.296、cx=367.215、cy=248.375，k1=-0.28340811、k2=0.07395907、p1=0.00019359、p2=0.0000176187114，直接来自本数据包 sensor.yaml。
- `body_T_cam0` 与 dataset T_BS 相同，平移为 [-0.0216401454975, -0.064676986768, 0.00981073058949] m；`estimate_extrinsic=0`。
- 已知同步数据固定 `estimate_td=0`、`td=0`。
- 原始单目 `matche_score_threshold=1.0` 改为 0.5（代码使用严格 `score > threshold`）；`ransacReprojThreshold=3.0`。
- 保留上游 IMU 调参 acc_n=0.1、gyr_n=0.01、acc_w=0.001、gyr_w=0.0001、g_norm=9.81007；它们与 sensor.yaml 的 noise density 不相同，未混称为完全一致。
- 原始 MEI 标定与在线估计配置的第一轮严重漂移，ATE RMSE 约 10,488.54 m，且未接受有效回环。切换数据包相机标定并固定已知外参/td 后成功；尚未单独隔离这三项改动各自的影响。
- 模型与词袋路径可在每轮 `euroc_mono_imu.yaml` 查看；绝对输出路径为该轮 `results/...`。

## 6. 可复用启动命令

正常重复运行（数据、依赖和词袋已就绪）：

```bash
cd /home/wyh/Project/Prometheus/Modules/SuperVINS
./scripts/reproduce_euroc.sh
```

该脚本构建、启动独立 ROS Master、VIO、Loop Fusion、RViz，完整播放 bag，记录资源、关闭本次创建的进程，验证输出并运行 EVO。每次创建新结果目录，成功验证后更新 `results/latest`。`--no-rviz` 可用于无显示环境。

分步执行：

```bash
./scripts/run_euroc.sh                  # 全序列，rate=1
./scripts/run_euroc.sh --duration 30   # 短诊断；不代表全序列成功
python3 tools/check_results.py results/<本轮目录>
./scripts/evaluate_euroc.sh results/<本轮目录>
```

手动分终端启动：每个终端先 `source scripts/env.sh`，它只影响当前 shell。

```bash
roscore -p 11321
rosparam set /use_sim_time true
rosrun supervins supervins_node "$SUPERVINS_WS/config/euroc_mono_imu.yaml"
rosrun supervins_loop_fusion supervins_loop_fusion_node "$SUPERVINS_WS/config/euroc_mono_imu.yaml"
roslaunch supervins supervins_rviz.launch
rosbag play --clock --delay=5 "$SUPERVINS_WS/data/V2_01_easy.bag"
```

自动脚本默认 Master `http://127.0.0.1:11321`。如果端口已被占用会拒绝启动，不复用/更改现有 ROS 会话。可通过 `SUPERVINS_MASTER_URI=http://127.0.0.1:11322` 选择另一空闲本机端口。

首次准备/迁移所需脚本：

```bash
./scripts/setup_ort.sh                       # 复制已有 ORT 1.23.2，并补齐版本一致的头文件
./scripts/setup_evo.sh                       # 工作空间 venv 中安装固定 EVO
./scripts/download_euroc.sh                  # 显式执行约 0.88 GB 下载
./scripts/prepare_euroc.sh                   # 生成 bag/真值；已有 bag 会拒绝覆盖
./scripts/extract_vocabulary_frames.py
./scripts/train_vocabulary.sh                # 已有词袋会拒绝覆盖
./scripts/build.sh
```

词袋训练随机初始化可能产生不同词袋；要精确复用本次实验应使用保留的词袋和哈希。ROS 回调/求解时限/线程调度也使相同配置的数值存在波动。

## 7. RViz、轨迹和完整性

最终运行处理全部 2,280 张左目图像，前端图像轨迹消息也是 2,280 条。初始化后输出 1,077 个 VIO 位姿、1,077 个密集修正位姿、192 个优化关键帧，9 次 LightGlue + PnP 回环接受，6 次真实 4DoF Ceres 求解。最终轮全部优化记录的 final cost 小于 initial cost。

Ceres 上游限制 max_num_iterations=5；最终 6 次求解中 1 次 CONVERGENCE、5 次 NO_CONVERGENCE。后者表示在迭代上限下未达到收敛标准，不能宣称求得全局最优；六次都实际完成迭代且降低了目标函数。

三个轨迹文件都为 8 列 TUM 格式（即使扩展名是 .csv）：`timestamp tx ty tz qx qy qz qw`，无 NaN/Inf、严格递增、四元数范数验证通过，整个数据集无 GPU Matcher 异常，最大密集轨迹刚体修正约 0.16056 m。证据：`results/latest/validation.json`、`loop.log`、`runtime_summary.json`。

| RViz 颜色 | topic |
|---|---|
| 绿色 VIO | /supervins_estimator/path |
| 橙色密集修正 | /supervins_loop_fusion/loop_corrected_path |
| 红色位姿图关键帧 | /supervins_loop_fusion/pose_graph_path |

RViz 实际窗口截图：[`results/latest/rviz_final.png`](results/V2_01_easy_20261012_151641/rviz_final.png)。轨迹对齐图：[`results/latest/evaluation/trajectories_xy.png`](results/V2_01_easy_20261012_151641/evaluation/trajectories_xy.png)；EVO PDF 见同目录。截图来自真实运行窗口，不是生成示意图。

## 8. EVO 定量结果与资源

EVO 1.29.0：translation APE，单位 m，SE(3) Umeyama 对齐，**没有 scale correction**，最大时间关联差 0.01 s。真值为 IMU/body 状态解；丢弃的是无法与真值关联的头尾位姿，没有人为裁剪高误差区间。

最终运行 `20261012_151641`：

| 轨迹 | ATE RMSE (m) | 真值关联位姿数 |
|---|---:|---:|
| VIO | 0.068518742 | 1,069 |
| 上游密集 loop-corrected | 0.068518733 | 1,069 |
| 优化关键帧 pose graph | 0.087683719 | 192 |
| 相同关键帧时间戳的 VIO | 0.068060007 | 192 |

此前成功运行 `20261012_151208`：VIO 0.060809395 m；密集修正 0.060809385 m；优化关键帧 0.046126436 m；相同关键帧 VIO 0.059344969 m（194 个关联关键帧）。本次没有挑选最小值当作唯一交付结果。

**关键限制：** 当前上游 `vio_callback()` 用一个最新 rigid drift 重建整条密集轨迹，所以 SE(3) 对齐后密集修正 ATE 与 VIO 相同，这是实现的数学结果。真正的非刚性位姿图优化在 `vio_loop.csv` 中。最终轮优化关键帧 ATE 比同时间戳 VIO 更差，而此前成功轮更好；不能声称本次回环稳定提升了精度。有限的自训练词袋、原算法参数、初始化及线程调度均是可能影响因素，尚未做因果消融。

最终频率：前端按时间戳 20.0 FPS、按墙钟约 20.07 FPS；VIO/密集轨迹约 10.0 Hz。上游 multiple_thread 分支硬编码每两帧进入一次估计器，YAML freq 不是它的覆盖开关。

1 秒采样，统计包括启动及播放结束后的排空时间；CPU 100% 表示一个逻辑核，进程及其子进程合计，RSS 求和可能重复计共享页：

| 进程组 | 平均 CPU (%) | P95 CPU (%) | 峰值 RSS (MiB) |
|---|---:|---:|---:|
| VIO | 58.77 | 83.17 | 1,074.77 |
| Loop Fusion | 6.17 | 11.79 | 1,054.61 |
| RViz（含实际子进程） | 35.23 | 48.73 | 401.64 |
| rosbag（含实际子进程） | 3.78 | 5.19 | 70.09 |

整卡平均 GPU 利用率 41.97%，峰值显存 5,341 MiB，平均功耗 91.47 W；包含桌面和其他应用，不能当作 SuperVINS 单独占用。nvidia-smi compute-process 记录中 VIO 峰值 1,282 MiB，Loop Fusion 峰值 444 MiB；RViz/桌面图形显存未由这项 compute-process 查询完整统计。

完整数据：[`results/latest/evaluation/summary.json`](results/V2_01_easy_20261012_151641/evaluation/summary.json)、`resources.json`。所有 ATE 数值直接来自 EVO 的 `*_ape.zip` / `*_ape.log`；每个对齐矩阵保存在 summary.json，完整对齐 TUM 为 `*_aligned.tum`。不同轨迹关联数量不同，故另提供相同关键帧 VIO 基线作可比评测。

## 9. D435i 真机适配准备（尚未实际运行）

EuRoC 成功后已完成接口与标定流程分析，没有把 EuRoC 标定用于真机，没有安装/启动新相机驱动。

- 图像：前端接收 mono8，并对其他可转换图像通过 cv_bridge 转 MONO8；8UC1 在主节点中改标 mono8。RGB 可转灰度，但首选 D435i 红外灰度图像作为初始适配方案。必须区分 raw 与 rectified：用整流图时从匹配 CameraInfo 的 P/R 获取新内参与坐标系，畸变设置为零，不能再次按 raw 标定去畸变。
- ROS1 legacy RealSense 驱动的常见图像为 `/camera/color/image_raw`、`/camera/infra1/image_rect_raw`，实际以 rostopic list 和 CameraInfo 为准。ROS1 分支 `ros1-legacy` 支持 Noetic；不要直接采用当前 ROS2 main 的参数表。
- IMU：不能把只有 gyro 或只有 accel 字段的 `/camera/gyro/sample`、`/camera/accel/sample` 单独当完整 IMU。选择 `unite_imu_method:=linear_interpolation`，使加速度插值到陀螺仪时间戳，使用完整 `/camera/imu`。按实际传感器支持 profile 选择频率，建议先测试 gyro 200 Hz，图像 20/30 Hz，检查实际频率再确定配置。
- 时间同步：保留 header.stamp，测量单调性、IMU 覆盖范围、抖动与长期时间偏移；`enable_sync` 主要组织图像流，不等于完成图像/IMU 标定。先录 bag，再用 Kalibr 等工具进行 camera–IMU 空间和时间标定。在线 td 是小偏差补偿，不应掩盖错误时钟来源。
- 外参：以实际发布的 IMU frame 和相机 optical frame 为基准，从对应 TF/工厂外参组合得到初始 `body_T_cam`，明确它应将 camera 坐标变换至 IMU/body 坐标。核对 accel/gyro 融合输出坐标、旋转方向和米制平移，再通过 camera–IMU 标定验证。
- 相机标定：使用最终选择的流、分辨率和曝光设置标定内参/畸变，必要时使用 camera_models Calibrations；立体方案还须两相机同步、内参和基线。重测 IMU 噪声/偏置，不复制本次 EuRoC IMU 参数。
- 频率：当前多线程实现对估计器每两帧取一帧，所以 30 Hz 图像通常产生约 15 Hz VIO；核实实际计数、时延与队列后再调整。神经网络时延不能代替整机频率测试。
- 在线外参：源码支持 estimate_extrinsic=0 固定、1 基于初值联合优化、2 无旋转先验时初始化旋转；estimate_td=1 支持在线时间偏移估计。建议先使用离线标定和固定参数验证运动，再在充分激励且有良好初值时评估在线优化。本次第一轮说明随意打开在线估计有实际风险。

参考：[RealSense ROS1 legacy README](https://github.com/realsenseai/realsense-ros/blob/ros1-legacy/README.md)、[ROS1 launch 参数](https://github.com/realsenseai/realsense-ros/blob/ros1-legacy/realsense2_camera/launch/rs_camera.launch)。实际设备、固件、时间同步和标定仍需真机验证。

## 10. 未完成与明确边界

- 未获得作者原始 SuperPoint DBoW3 词袋，无法声称严格重现论文精度。
- 未做原始 VINS-Fusion 对比、完整 EuRoC 全部序列、多次统计置信区间或不同词袋的消融。
- 未做 D435i 真机标定或实测；上面的内容是适配准备。
- 未修改上游密集轨迹的单一刚体修正语义，也没有宣称密集输出本身降低 SE(3)-对齐 ATE。
- 未将 Ceres 迭代上限下的 NO_CONVERGENCE 报告写成完全收敛。
- 未测量独占 GPU 的整卡负载；保留背景应用，并提供核心进程显存数据。

这些边界不影响已实际验证的原生编译、GPU 深度前端、持续 VIO、LightGlue 回环、位姿图迭代、RViz 和 EVO 交付。
