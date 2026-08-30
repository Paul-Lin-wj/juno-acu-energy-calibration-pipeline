# calibsel — JUNO 刻度事例挑选（γ 单例链 + AmC 关联对支线）

γ 单例链：把 JUNO ReProd26B 刻度数据从 EDM（或 ESD）一路处理成
`peakfit` 可直接使用的 `Run{N}_SelectionResult.npz`
（OMILREC 重建能量/顶点 + 26B Finalcorrection + 单事件源 EFV 挑选）。

AmC 支线（Stage 3c，2026-08-27 并入）：`(prompt, delayed)` 关联对挑选 →
`correlation_result_RUN{N}.npz`（nH/nC/O16 三峰能量数组，供
`peakfit/pipeline/run_amc_fit_all.py`）。详见
[README.amc.md](README.amc.md) / [PROVENANCE.amc.md](PROVENANCE.amc.md)。

**源分流（2026-08-29）**：`run_all.py` 的 Stage 1+2（EDM→NPZ→26B 修正）对源
类型无关，是两条支线的公共前段——AmC 族 run（`paths.is_amc_source`：源名带
Am/Cf 标签）走到修正 npz 即收尾（γ 的单例挑选对它们无意义），产出
`npz_corrected/RUN{N}.npz`（含自动本底 run）直接喂 `run_amcsel_all.py`；
γ run 继续 Stage 3/4。`run_all.py --runs 10110` 与 `--runs 12370` 同一入口。

两条支线都对每次运行做审计级留档（含**全部挑选 cut 条件**）。
γ 链代码溯源与逐位一致性审计见 `PROVENANCE.md`；使用说明见 `skills/`。

## 快速开始

```bash
cd standalone_calibsel
bash setup_env.sh        # 一次性：建 .venv（stage 1-4 纯 Python）

bash run_pipeline.sh                # 默认 run（12370），默认模式 from-edm
bash run_pipeline.sh 12370 12295    # 指定多个 run
bash run_pipeline.sh 12370 --full-esd --slice 3   # 冒烟：本机重建前 3 个 ESD
```

**默认模式 `from-edm`**（即原 `--skip-esd`）：直接从 lustrefs 上现成的
ReProd26B EDM 分块（`config/paths.py: REMOTE_EDM_DIR`，2799 块）开始，
不需要 CVMFS/JUNOSW/EOS。`--full-esd` 才会做本机 ESD→EDM 重建。

## 输出目录（每次运行一个时间戳目录）

```
output/<YYYYmmdd_HHMMSS>/
├── results/
│   ├── npz_raw/RUN{R}.npz                       # Stage 1
│   ├── npz_corrected/RUN{R}.npz                 # Stage 2（含本底 run）
│   ├── selection_npz/Run{R}_SelectionResult.npz # ★ fitter 输入
│   └── timestamps/Timestamp_{wo,E}cut/RUN{R}.txt
├── figures/
│   ├── selection/*.png                          # 挑选 QA 图
│   └── physics_qa/Run{R}_physics_qa.{png,json}  # 物理特征 QA（人类判读）
├── cuts/{R}_cuts.json + summary.md              # ★ 本次全部挑选条件
├── code/                                        # ★ 完整代码快照（含 sha256.json）
├── logs/stage*.log                              # 各 stage 完整输出
├── code_snapshot/ + sha256.json                 # 算法文件快照（cut 逻辑溯源）
├── run_log.md / run_log.json / config_snapshot.json / console.log
└── （run_log 含 Audit 段：结束完整性审计结果）
```

**结束审计（自动）**：每次运行结束时自动完成——① 把完整代码树复制到 `code/`（附 `code/sha256.json`）；② 校验 code 快照与工作树逐字节一致、全部关键输出存在；③ 结果写入 `run_log.json -> audit`。失败时：脚本模式 `exit 3`（不发布 `latest`），agent 模式打印 `[AUDIT] WARNING`。

## 目录结构

```
standalone_calibsel/
├── run_pipeline.sh          # 一键入口（→ pipeline/run_all.py）
├── setup_env.sh             # 建 .venv + 可选 libpcre
├── requirements.txt
├── config/paths.py          # ★ 唯一需要按环境修改的文件（含默认模式）
├── pipeline/
│   ├── run_all.py           # 总调度（stage 1-4 + 本底自动补跑）
│   ├── run_logger.py        # 审计级运行留档（md/json/快照/sha256）
│   └── cuts_parser.py       # 挑选条件解析归档
├── src/                     # ★ 算法文件（审计冻结，禁止改动）
│   ├── list_esd.py          #   Stage 0a: xrdfs ESD 清单
│   ├── esd_to_edm.py        #   Stage 0b: ESD→EDM（MySimpleTag）
│   ├── convert_edm_to_npz.py#   Stage 1: EDM→NPZ
│   ├── apply_final_correction.py # Stage 2: 26B 修正
│   ├── combine_selection.py #   Stage 3: 挑选（cut 定义所在）
│   └── local_utils.py       #   内联工具函数
├── input/correction/        # 26B 修正 API + 模型数据（md5 校验副本）
├── calib_run_info -> ../runcheck/data  # run 事实源表真身在 runcheck/（链外
│                            # 用户级目录）；符号链接保冻结 src 路径不变
├── tools/
│   ├── make_physics_qa.py   # 生产 QA：单 run 物理特征图（无需参考）
│   └── make_audit_report.py # 备用：与原链路逐位比对报告
├── skills/                  # 使用/调整/排障/留档说明（10 篇）
├── lib/libpcre.so.1         # 仅 --full-esd 需要
└── data/                    # 手动运行 src/ 时的传统输出位（流水线不写这里）
```

## 流水线阶段

| Stage | 脚本 | 说明 |
|---|---|---|
| 0（可选 `--full-esd`） | `src/list_esd.py` + `src/esd_to_edm.py` | ESD→EDM 重建，需 CVMFS+JUNOSW，慢 |
| 1 | `src/convert_edm_to_npz.py` | EDM 分块合并 → `RUN{R}.npz` + LivingTime |
| 2 | `src/apply_final_correction.py` | 26B 修正：r-bias 顶点 + 空间 + 时间 + phase 能标 |
| 2b | 自动 | 本底 run 的 Stage 1-2（映射表驱动） |
| 3 | `src/combine_selection.py` | MuonVeto + 稳健 ROI + Z-cut + EFV 椭圆 + 能量窗 |
| 4 | `tools/make_physics_qa.py` | 物理特征 QA 图（8 面板）+ JSON 摘要 |

## 依赖

| 环节 | 依赖 |
|---|---|
| Stage 1-4（默认） | `.venv`：numpy/pandas/scipy/matplotlib/uproot + lustrefs EDM 只读 |
| Stage 0（`--full-esd`） | CVMFS J26.3.1 + JUNOSW_MyAlgz + EOS xrootd 可达 |

## 与 fitter 的衔接（一次配置，自动跟进）

```bash
# standalone_fitter/config/paths.py:
DATA_INPUT_PATH = "<本项目>/output/latest/results/selection_npz"
```

流水线每次**完整成功**后会把 `output/latest` 原子切换到本次时间戳目录
（失败不会动它），fitter 无需再改路径。要锁定某一历史批次时，把路径里的
`latest` 换成具体 `output/<时间戳>/` 即可。

已验证（2026-08-24）：用本项目输出跑 fitter，Ge68 拟合 mu=0.9102 MeV、
σ/E=3.54%，与历史结果全部字段一致。

## 数值保证

同一 EDM 输入下，本链路输出与原生产链路**逐位一致**（2026-08-24 实测：
raw/corrected/selection 三级 npz 共 25 字段 maxdiff=0）。任何对 `src/`
或 `input/correction/` 的改动都会使该保证失效，必须重新审计
（`skills/10_audit_verification.md`）。
