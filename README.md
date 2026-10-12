# SuperVINS 2.0

ROS1 视觉惯性 SLAM：SuperPoint 特征提取、LightGlue 匹配、VIO、回环检测、位姿图优化与 RViz 可视化。

## 环境要求

| 依赖 | 版本要求 |
|---|---|
| 系统 / ROS | Ubuntu 20.04、ROS1 Noetic、Catkin |
| 编译器 / 数学库 | GCC 9 / C++17、Eigen 3.3、Ceres 2.1 |
| 图像库 | OpenCV 4.2 |
| GPU 推理 | NVIDIA GPU、ONNX Runtime GPU 1.23.2 |
| RTX 5070 Ti 配套环境 | CUDA 12.8、cuDNN 9.x、支持该 GPU 的驱动 |
| Python | ROS 使用系统 Python 3，依赖 numpy、opencv、yaml、psutil |

将 ONNX Runtime 1.23.2 SDK 放在 `deps/onnxruntime-1.23.2/`，或从已有 SDK/Python 包复制库：

```bash
./scripts/setup_ort.sh ./deps/ort-source/lib
# 已安装 onnxruntime-gpu==1.23.2 的 Python 环境也可自动识别：
./scripts/setup_ort.sh
```

系统依赖使用默认安装位置；自定义安装可通过 `ROS_SETUP_FILE`、`CUDA_HOME`、`Ceres_DIR`、`ONNXRUNTIME_ROOTDIR` 指定。工程内部路径均从工程或 YAML 所在目录解析，不依赖下载位置和启动时的工作目录；更换下载目录后在新目录编译。

## 配置要求

默认配置：`config/euroc_mono_imu.yaml`。相机标定使用同目录的 `cam0_euroc.yaml`、`cam1_euroc.yaml`。

- 图像 `/cam0/image_raw`，IMU `/imu0`；单目 + IMU，图像尺寸 752×480。
- 模型与词袋已放在 `src/SuperVINS/`；YAML 中模型、词袋、标定和输出路径都相对于该 YAML。
- 输出保存到 `results/`；启动脚本为每次运行生成独立目录和相对路径配置。
- 更换相机或数据集时，修改话题、图像尺寸、内参、相机–IMU 外参及 IMU 参数。

## 下载数据集

```bash
git clone https://github.com/Leonard-WYH/SuperVINS.git
cd SuperVINS
./scripts/download_euroc.sh   # 下载 EuRoC V2_01_easy，约 0.88 GB
./scripts/prepare_euroc.sh    # 从原始图像/IMU 生成 ROS bag 与真值
```

也可将已有 bag 放到 `data/V2_01_easy.bag`。下载与转换输出位于工程 `data/`，数据集不纳入 Git。

## 脚本启动

```bash
./scripts/build.sh           # Release 编译，默认 -j8
./scripts/run_euroc.sh       # ROS Master、VIO、Loop Fusion、RViz 和 rosbag
# 无图形界面：
./scripts/run_euroc.sh --no-rviz
```

脚本可通过完整或相对路径从其他目录执行，默认 ROS Master 端口为 `11321`。可用 `--bag data/其他数据.bag`、`--rate 0.5` 指定工程内数据和播放速率。

可选轨迹评测：

```bash
./scripts/setup_evo.sh python3.10
./scripts/evaluate_euroc.sh results/本次运行目录
```

基于 [SuperVINS](https://github.com/luohongk/SuperVINS)，遵循 [GPL-3.0](LICENSE)。
