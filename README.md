# SuperVINS 2.0 中文复现

基于 [官方 SuperVINS](https://github.com/luohongk/SuperVINS) 的 ROS1 原生复现：SuperPoint 提取、LightGlue GPU 匹配、视觉惯性里程计、回环检测、位姿图优化与 RViz 可视化。

已在 **Ubuntu 20.04 + ROS Noetic + RTX 5070 Ti** 上实际完成 EuRoC `V2_01_easy` 全序列测试。使用 CUDA 12.8、cuDNN 9.10.2、ONNX Runtime GPU 1.23.2、OpenCV 4.2、Ceres 2.1，无需 Docker。

## 实测结果

- 处理 2,280 帧，前端约 **20 FPS**，VIO 约 **10 Hz**。
- 最终运行接受 **9 次 LightGlue 回环**，执行 **6 次位姿图优化**。
- VIO ATE RMSE：**0.06852 m**；优化关键帧：**0.08768 m**。

原仓库未提供所需词袋，本仓库包含自训练 SuperPoint 词袋，因此不是论文实验的严格等价复现。上游密集修正轨迹只应用统一刚体变换，对齐后 ATE 与 VIO 相同；最终轮关键帧优化未改善精度。详细配置、失败排查、两轮结果和 D435i 适配准备见 [REPRODUCTION.md](REPRODUCTION.md)。

[轨迹对齐图](results/V2_01_easy_20261012_151641/evaluation/trajectories_xy.png) · [RViz 截图](results/V2_01_easy_20261012_151641/rviz_final.png)

## 快速运行

先安装 ROS Noetic、OpenCV/Eigen、Ceres 2.1，以及与 GPU 兼容的 CUDA/cuDNN。准备已有 ONNX Runtime GPU **1.23.2** 库和 Python 3.10，然后执行：

```bash
git clone https://github.com/Leonard-WYH/SuperVINS.git
cd SuperVINS

# 传入已有 ORT 1.23.2 的 lib/capi 目录，以及 Python 3.10 路径
./scripts/setup_ort.sh /path/to/onnxruntime/capi
./scripts/setup_evo.sh /path/to/python3.10

# 下载约 0.88 GB 的 V2_01_easy，生成原生 ROS bag
./scripts/download_euroc.sh
./scripts/prepare_euroc.sh

# 编译、完整播放、可视化、验证与 EVO 评测
./scripts/reproduce_euroc.sh
```

脚本使用独立 ROS Master 端口 **11321**，自动生成本次配置并保存结果至 `results/`。无显示环境可加 `--no-rviz`。模型与词袋已随源码提供；数据集、ORT 二进制、Python 环境和编译产物不提交到 Git。

## 目录

- `src/SuperVINS/`：官方源码、模型及必要兼容修改。
- `scripts/`、`tools/`：依赖准备、启动、GPU 测试及评测工具。
- `REPRODUCTION.md`：完整复现记录。
- `results/latest/`：已验证的轨迹、EVO 摘要与截图（运行后更新）。

上游提交：`e9689cf72cebbc7901b110ff201daedf27b0c3ff`。项目遵循 [GPL-3.0](LICENSE)，保留上游作者与第三方声明。
