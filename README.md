# JUNO 刻度数据流水线（自包含单仓库）

本仓库把两个独立项目**合并为一个自包含仓库**（普通目录，非 submodule），
覆盖从 ESD/EDM 到能谱拟合的完整链路。**普通 `git clone` 即可拿到全部内容**。

```
calib_pipeline_suite/
├── esd2npz/     # EDM/ESD → NPZ → 26B 修正 → 挑选（SelectionResult.npz）
│                #   含挑选 cut 留档与结束完整性审计（code/ 快照 + audit）
├── fitter/      # 能谱拟合：μ / σ/E / χ²，ENL 风格分辨率汇总
├── run_pipeline.sh   # ★ 联合驱动：依次跑 esd2npz → fitter
└── output/           # ★ 联合输出（不入库）
```

## 克隆

```bash
git clone git@github.com:Paul-Lin-wj/calib_pipeline_suite.git
```

> 自包含仓库：无子模块，普通克隆即全量。

## 一键联合运行

```bash
bash run_pipeline.sh                 # 默认 run（esd2npz DEFAULT_RUNS = 12370）
bash run_pipeline.sh 12370 12295     # 指定多个刻度 run
RUNS="12370 12295" bash run_pipeline.sh
```

脚本依次驱动：**esd2npz（EDM→挑选）→ fitter（拟合）**，两个项目的 output
收进**同一个时间戳目录**：

```
output/<YYYYmmdd_HHMMSS>/
├── esd2npz/     # results/(npz_raw, npz_corrected, selection_npz, timestamps)
│                # figures/  cuts/  logs/  code/（完整代码快照）
│                # run_log.{md,json}  config_snapshot.json
└── fitter/      # results/  figures/  enl_style_resolution.*
                 # code/  run_log.{md,json}  config_snapshot.json
```

衔接自动完成：fitter 直接读取**同批** esd2npz 的
`output/<ts>/esd2npz/results/selection_npz`，不依赖 `output/latest`。

### 单项目独立运行

```bash
cd esd2npz && bash run_pipeline.sh 12370        # 默认布局 output/<ts>/
cd esd2npz && bash run_pipeline.sh 12370 --out-dir <dir>   # 指定输出
cd fitter && .venv/bin/python pipeline/run_fit_all.py \
    --input-dir <selection_npz目录> --out-dir <输出目录>    # 拟合单独跑
```

## 首次环境准备（每台机器一次）

```bash
cd esd2npz && bash setup_env.sh   # 建 .venv（Stage 1-4 纯 Python）
cd ../fitter && bash setup_env.sh # 建 .venv（拟合）
```

## 内容与上游的关系

- `esd2npz/` 对应独立仓库 `standalone_esd2npz`（仍在线，本仓库为内容快照）
- `fitter/` 对应独立仓库 `juno_calibration_acu_gamma_source`（仍在线）
- 两项目的运行/审计文档见各自子目录的 `README.md` / `PROVENANCE.md` / `skills/`

## 运行产物与仓库边界

- `output/`、`esd2npz/data/`、`.venv/`、`TMP/`、`__pycache__/` 等运行产物
  不入库（由顶层与子目录 `.gitignore` 覆盖）
- 每次运行自带的 `code/` 完整代码快照与 `audit` 记录是**运行时产物**，
  也不入库（`esd2npz/.gitignore` 已忽略）
