# JUNO ACU 刻度数据流水线

> **[English Version](README.en.md)**

## 项目简介

JUNO（江门中微子实验）ACU（自动刻度单元）伽马源刻度数据的完整处理流水线：
把探测器原始重建数据一路处理到**能谱拟合结果**（峰位 μ、分辨率 σ/E），覆盖
Ge68 / Cs137 / Mn54 / Co60 / K40 五种单事件刻度源。

```
ESD / EDM（原始重建数据）
   │  esd2npz/
   ▼
NPZ（每 run 合并事件 + LivingTime）
   │  26B Finalcorrection（r-bias 顶点 + 空间 + 时间 + phase 绝对能标）
   ▼
修正后 NPZ
   │  挑选：MuonVeto → 稳健 ROI → Z-cut → EFV 椭圆 → 能量窗
   ▼
Run{N}_SelectionResult.npz（fitter 输入）
   │  fitter/
   ▼
拟合：MC 模板卷积 + Minuit → μ / σ / χ² + ENL 分辨率汇总图
```

每一步的挑选条件（ROI、z_limit、能量窗等）随运行自动归档；每次运行还附带
**完整代码快照**与**结束完整性审计**，保证结果可溯源。

## 目录结构

| 目录/文件 | 作用 |
|---|---|
| `esd2npz/` | 数据处理流水线：EDM→NPZ→26B 修正→挑选。`src/` 为算法代码（自原生产链路逐行移植，输出与原链路逐位一致）；`pipeline/` 为调度与审计留档；`input/correction/` 为 26B 修正模型；`calib_run_info/` 为 run→源/本底映射 |
| `fitter/` | 能谱拟合：`src/FastGe68Fitter.py`（Ge68，MC 模板缓存，~4 s）、`src/FastSourceFitter.py`（Cs137/Mn54/Co60/K40 通用，~0.5 s）、`fitters/`（MC 模板与经典版回退）、`pipeline/run_fit_all.py`（主流程） |
| `run_pipeline.sh` | 一键依次驱动 `esd2npz` → `fitter`，两个项目的输出收进同一个时间戳目录 |
| `output/` | 运行输出（不入库），见下文布局 |

## 物理背景

- **源**：Ge68（正电子湮灭，双 511 keV）、Cs137（0.662 MeV）、Mn54（0.835 MeV）、
  Co60（1.173+1.333 MeV 双 γ 级联）、K40（1.461 MeV）。拟合用 E_true 作对照。
- **能量修正（26B）**：对重建能量施加顶点 r-bias 修正、二维空间非均匀性修正、
  时间稳定性修正与 phase 绝对能标（P1/2≈0.99340，P3/4≈0.99743）。
- **挑选（减本底）**：刻度 run 与映射的本底 run 按 LivingTime 归一为事例率后
  相减，用 R_diff 曲线做稳健判据；EFV 椭圆体积窗选事例，能量窗取峰拟合 μ±3σ。
- **拟合模型**：Compton MC 模板（卷积能量分辨率 σ(E)=√((a/√E)²+b²+(c/E)²)·E）+
  光电峰高斯 + C14 堆叠；输出 μ、σ/E、χ²/ndf。

## 快速开始

```bash
# 环境准备（每台机器一次）
cd esd2npz && bash setup_env.sh    # 建 .venv（Stage 1-4 纯 Python）
cd ../fitter && bash setup_env.sh  # 建 .venv（拟合）

# 一键联合运行：esd2npz（挑选）→ fitter（拟合）
bash run_pipeline.sh                 # 默认 run 12370（Ge68）
bash run_pipeline.sh 12370 12295     # 指定多个刻度 run
```

输出：

```
output/<YYYYmmdd_HHMMSS>/
├── esd2npz/     # results/(npz_raw, npz_corrected, selection_npz, timestamps)
│                # figures/  cuts/（挑选条件）  logs/  code/（代码快照）
│                # run_log.{md,json}（含 audit）  config_snapshot.json
└── fitter/      # results/(RUN{N}_{源}.npz)  figures/  enl_style_resolution.*
                 # code/  run_log.{md,json}  config_snapshot.json
```

fitter 自动读取**同批** esd2npz 的 `results/selection_npz`，无需手动衔接。

单项目独立运行：

```bash
cd esd2npz && bash run_pipeline.sh 12370 --out-dir <目录>
cd fitter && .venv/bin/python pipeline/run_fit_all.py \
    --input-dir <selection_npz目录> --out-dir <输出目录>
```

## 留档与审计

- **挑选条件**：`cuts/{RUN}_cuts.json`（ROI、Step-1 能量区、z_limit、EFV 计数、
  最终能量窗）+ `cuts/summary.md` 多 run 汇总
- **代码快照**：每次运行把完整代码树复制到 `code/`（附 `code/sha256.json`），
  运行所用的算法版本逐字节可查
- **结束审计**：校验 code 快照与工作树逐字节一致、全部关键输出存在，结果在
  `run_log.json -> audit`；失败时脚本模式 `exit 3`，agent 模式打印警告
- **运行日志**：`run_log.{md,json}`（系统/依赖/配置指纹/每 run 事件统计/
  输入输出 SHA-256）

## 文档索引

- 数据处理与溯源：`esd2npz/README.md`、`esd2npz/PROVENANCE.md`
- 拟合设计与日志规范：`fitter/README.md`、`fitter/DESIGN_REPORT.md`
- 使用手册：两项目各自 `skills/`（环境/配置/运行/排障/审计）
