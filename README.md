# JUNO ACU 刻度数据流水线

> **[English Version](README.en.md)**

## 项目简介

JUNO（江门中微子实验）ACU（自动刻度单元）伽马源刻度数据的处理流水线。
能量非线性/分辨率测量的完整物理链路为：

> 波形重建 → 事例重建 → 事例挑选（刻度源 & 连续谱核素）→ 峰位拟合/连续谱拟合
> → 非线性曲线拟合 → E_true = f(E_rec)

本仓现已覆盖 **EDM → E_true=f(E_rec)** 主链（含 26B 能量修正、事例挑选、物理 QA、
峰位拟合与非线性全局拟合），刻度源覆盖 Ge68 / Cs137 / Mn54 / Co60 / K40
五种单能源 + AmC 关联对三峰（n-H / n-12C / O16，`calibsel` AmC 支线）；连续谱备谱仍按
**并入规划**推进（见下方覆盖一览）。

```text
完整物理链路与覆盖状态
（✅ 本仓已有 ｜ 🔶 代码已有·待并入 ｜ ⚠️ 外部依赖·可选接入 ｜ ❌ 暂缺，先用已有数据）

✅ 波形+事例重建（rtraw → ESD：waverec 刻度 + OMILREC 顶点/能量）
   │                                                 【可选模块 `recon`：官方
   │                                                  tut_rtraw2rec（CVMFS J26.1.1）
   │                                                  编排包装 + OMILRECV2 overlay
   │                                                  开关（--impl omilrecv2|baseline）；
   │                                                  默认关闭——γ 链 Stage 0 --full-esd
   │                                                  读生产 ReProd26B ESD 走 MySimpleTag】
   ▼  calibsel/
✅ Stage 1   EDM → NPZ（每 run 合并事件 + LivingTime）
   ▼
✅ Stage 2   26B Finalcorrection（r-bias 顶点 + 空间 + 时间 + phase 绝对能标；
   │         映射的本底 run 自动处理）
   ▼
✅ Stage 3   刻度源事例挑选（MuonVeto → 稳健 ROI → Z-cut → EFV 椭圆 → 能量窗；
   │         刻度 run 与本底 run 按 LivingTime 归一为事例率后相减）
✅ Stage 3c  AmC 相关对挑选（prompt–delayed 时间窗 + 距离关联 → nH/nC/O16 事例）
   │                                                 【calibsel AmC 支线：correlate_selection
   │                                                  原样并入（仅 2 行 import 本地化），
   │                                                  输出与生产侧逐数值一致】
❌            连续谱核素挑选                          【备谱 code 暂缺；暂以已有数据
   │                                                  作外部输入（契约 + 清单）】
   ▼
   Run{N}_SelectionResult.npz / correlation_result_RUN{N}.npz（peakfit 输入）
   ▼  peakfit/
✅ 刻度源峰位拟合（MC 模板卷积 + Minuit → μ / σ/E / χ²）
   │         + ENL 风格分辨率汇总图（参考曲线为固定参数，未拟合）
✅ n-H / n-12C / O16 峰位拟合                        【peakfit/pipeline/run_amc_fit_all：
   │                                                  nH/nC 纯高斯（NhnCFitter 逐字节
   │                                                  移植）+ O16 模板分解（O16Fitter）】
❌ 连续谱拟合                                         【dybmodel 已内置 B12/C10/C11/
   │                                                  Michel 拟合机器；输入暂用已有数据】
   ▼  nlfit/（新模块，已接入）
✅ Stage 4b  外部数据契约校验（连续谱 + 过渡期 nH/nC/O16 历史值，
   │         MANIFEST sha256）                          【nH/nC/O16 已由 AmC 链实测提供】
   ▼
✅ Stage 5   聚合：per-source μ/σ → meanEscaleEres 表 → gamma_AllPhase.dat
   │                                                 【纯 Python；peakfit 缺源时自动
   │                                                  钉历史值并告警】
   ▼
✅ Stage 6   非线性全局拟合（dyb 模型，E_rec/E_true vs E_true）
   │                                                 【wrap ENL_agent/
   │                                                  fitter_energynl_dybmodel（C++）；
   │                                                  沙箱 + 2 处非物理补丁，
   │                                                  cvmfs J26.1.1，能力探测】
   ▼
✅ Stage 7   E_rec → E_true 反演 → E_true = f(E_rec) 查询表
                                                     【纯 Python（e⁻/e⁺/γ 三条曲线，
                                                      往返误差 ≤2e-5）】
```

### 覆盖一览

| 物理链路阶段 | 状态 | 位置 / 说明 |
| --- | :---: | --- |
| 波形重建 | ❌ | 上游 JUNOSW 产物；规划以可选 stage 包装接入 |
| 波形+事例重建 | ✅（可选） | `recon` 模块：官方 tut_rtraw2rec 编排包装 + OMILRECV2 overlay 开关（rtraw→ESD，xrootd 读 EOS 原始档）；默认关闭，`calibsel` Stage 0 `--full-esd` 走生产 ESD→MySimpleTag→EDM。⚠️ 冻结 tag 为 26A，与生产 26B ESD 的差异待量化 |
| 刻度源事例挑选 | ✅ | `calibsel` Stage 1–3 + Stage 4 物理 QA（8 面板图 + JSON） |
| AmC 相关对挑选（n-H/n-12C/O16） | ✅ | `calibsel` AmC 支线（correlate_selection 原样并入，行为与生产侧逐数值一致；中心 run 三峰 vs AllPhase 差 ≤1.2%） |
| 连续谱核素挑选 | ❌ | 备谱 code 暂缺；暂以已有数据作外部输入（`nlfit` Stage 4b MANIFEST 契约） |
| 刻度源峰位拟合 | ✅ | `peakfit`（Fast 版 Ge68 ~4 s、其余 ~0.5 s；经典版回退） |
| n-H/n-12C/O16 峰位拟合 | ✅ | `peakfit/pipeline/run_amc_fit_all`：nH/nC 纯高斯（`NhnCFitter` 逐字节移植）+ O16 模板分解（`O16Fitter`；HESSE 状态如实入 run_log） |
| 连续谱拟合 | ❌ | dybmodel 已内置 B12/C10/C11/Michel 拟合机器；上游输入暂用已有数据 |
| 非线性曲线拟合 | ✅ | `nlfit` Stage 6：wrap `ENL_agent/fitter_energynl_dybmodel`（沙箱 + 行为锁定） |
| E_true=f(E_rec) 反演 | ✅ | `nlfit` Stage 7：纯 Python，e⁻/e⁺/γ 三条查询曲线 |

### 并入规划

| 优先级 | Stage | 内容 | 来源 | 方式 | 状态 |
| --- | --- | --- | --- | --- | --- |
| ★★★ | 4b | 外部数据契约（连续谱 + 过渡期 nH/nC/O16 历史值） | dybmodel `necessaryfiles/` 等 | 校验 + MANIFEST（SHA-256） | ✅ 已落地（`nlfit`） |
| ★★★ | 5 | 聚合 per-source μ/σ → `gamma_AllPhase.dat` | ENL_agent `glue/gen_gamma_dat.py` | port（纯 Python） | ✅ 已落地（`nlfit`） |
| ★★★ | 6 | 非线性全局拟合 | `fitter_energynl_dybmodel` | wrap（C++，cvmfs J26.1.1；能力探测） | ✅ 已落地（`nlfit`） |
| ★★☆ | 7 | E_rec→E_true 反演出查询表 | 新写 | 纯 Python（单调性 + 往返校验） | ✅ 已落地（`nlfit`） |
| ★☆☆ | 3c/3b | AmC 相关对挑选 + nH/nC/O16 峰位拟合 | `correlate_selection` + `AmC_nH-nC_fitter` / 本仓 `O16Fitter` | `calibsel` AmC 支线（原样并入）+ `peakfit` `run_amc_fit_all`；nlfit PEAKS 三峰 provider=`amc` | ✅ 已落地 |
| ☆☆☆ | 0/-1 | 波形/事例重建全链 | JUNOSW 官方链 + `omilrec_opt/omilrecv2`（overlay） | 独立 `recon` 模块编排包装（`--impl omilrecv2\|baseline`；与 ReProd26B 不逐位一致，tag 口径待对齐） | ✅ 已落地（2026-08-28，默认关） |

新 stage 均沿用现有 chassis（RunLogger / code snapshot / audit / exit code /
`--launched-by agent`），顶层 `run_pipeline.sh` 已扩展为 recon（可选）→ calibsel →
peakfit → nlfit 四段。姊妹工作区 `/datafs/users/wujxy/agent-sci/ENL_agent/`（DSH 编排，
`.dsh/skills/`）仍是 🔶 待并入模块的代码来源，同时 dybmodel 以**只读 wrap**
方式被 `nlfit` 调用（沙箱自动重建，输入输出 sha256 记录在案）。

每一步的挑选条件（ROI、z_limit、能量窗等）随运行自动归档；每次运行还附带
**完整代码快照**与**结束完整性审计**，保证结果可溯源。

## 目录结构

| 目录/文件 | 作用 |
| --- | --- |
| `recon/` | 【可选 Stage −1】rtraw→ESD 本地重建：官方 `tut_rtraw2rec`（CVMFS J26.1.1）编排包装 + OMILRECV2 overlay 开关（`--impl omilrecv2\|baseline`）；纯编排零算法代码，flag 集冻结于 `config/paths.py`（见 `PROVENANCE.md`；⚠️ tag 26A vs 生产 26B 待对齐） |
| `calibsel/` | 刻度事例挑选（γ 单例链 + AmC 关联对支线）：γ 链 EDM→NPZ→26B 修正→挑选（`src/` 算法自原生产链路逐行移植，输出与原链路逐位一致）；AmC 支线 `src/amc/` 为 correlate_selection 原样并入（仅 2 行 import 本地化，行为与生产侧逐数值一致，见 `PROVENANCE.amc.md`）；`pipeline/run_all.py`（γ，`--esd-list-dir` 吃 recon 衔接清单）与 `pipeline/run_amcsel_all.py`（AmC）为调度与审计留档 |
| `peakfit/` | 能谱拟合：`src/FastGe68Fitter.py`（Ge68，MC 模板缓存，~4 s）、`src/FastSourceFitter.py`（Cs137/Mn54/Co60/K40 通用，~0.5 s）、`fitters/`（MC 模板与经典版回退）、`pipeline/run_fit_all.py`（主流程）、`pipeline/run_amc_fit_all.py`（AmC 三峰：nH/nC 纯高斯 `NhnCFitter` + O16 模板分解） |
| `nlfit/` | 非线性全局拟合（Stage 4b/5/6/7）：外部数据契约、7 峰聚合 `gamma_AllPhase.dat`、dybmodel C++ wrap（沙箱自动重建 + 行为锁定）、E_rec→E_true 反演查询表；`external_inputs/` 为过渡期外部数据契约 |
| `run_pipeline.sh` | 一键依次驱动 `recon`（可选，`RECON_IMPL` 开启）→ `calibsel`（γ+AmC 挑选）→ `peakfit`（拟合）→ `nlfit`，各项目的输出收进同一个时间戳目录 |
| `output/` | 运行输出（不入库），见下文布局 |

## 物理背景

- **源**：Ge68（正电子湮灭，双 511 keV）、Cs137（0.662 MeV）、Mn54（0.835 MeV）、
  Co60（1.173+1.333 MeV 双 γ 级联）、K40（1.461 MeV）。拟合用 E_true 作对照。
- **AmC 中子源**（²⁴¹Am–¹³C）：¹³C(α,n)¹⁶O* 同时给出 O16 6.129 MeV
  （prompt）与慢化中子俘获峰 n-H 2.2233 MeV、n-12C 4.945 MeV（delayed），
  经 prompt–delayed 相关对挑选（`calibsel` AmC 支线，俘获时间 τ≈211 μs）后由
  `peakfit` 拟合，为非线性拟合 7 峰输入提供其中 3 个。注意 ACU AmC 沿 z 轴
  扫描（±17.3 m）：与 AllPhase 历史值对比须用中心 run（边缘 run 有 ~% 量级
  位置偏移，属真实效应）。
- **能量修正（26B）**：对重建能量施加顶点 r-bias 修正、二维空间非均匀性修正、
  时间稳定性修正与 phase 绝对能标（P1/2≈0.99340，P3/4≈0.99743）。
- **挑选（减本底）**：刻度 run 与映射的本底 run 按 LivingTime 归一为事例率后
  相减，用 R_diff 曲线做稳健判据；EFV 椭圆体积窗选事例，能量窗取峰拟合 μ±3σ。
- **拟合模型**：Compton MC 模板（卷积能量分辨率 σ(E)=√((a/√E)²+b²+(c/E)²)·E）+
  光电峰高斯 + C14 堆叠；输出 μ、σ/E、χ²/ndf。

## 快速开始

```bash
# 环境准备（每台机器一次）
cd calibsel && bash setup_env.sh    # 建 .venv（Stage 1-4 纯 Python）
cd ../peakfit && bash setup_env.sh # 建 .venv（拟合）
cd ../nlfit  && bash setup_env.sh  # 建 .venv（聚合/反演；Stage 6 另需自建容器或 cvmfs ROOT）

# 一键联合运行：recon（可选）→ calibsel（γ 单例 + AmC 关联对挑选）→ peakfit（拟合）
#                → nlfit（非线性拟合+反演）
bash run_pipeline.sh                 # 默认 γ run 12370（Ge68）+ AmC run 10110
bash run_pipeline.sh 12370 10110     # 指定 run（按源类型自动路由 γ/AmC 分支）
NLFIT_FLAGS="--skip-dybmodel" bash run_pipeline.sh   # 无容器时跳过 Stage 6/7
RECON_IMPL=omilrecv2 bash run_pipeline.sh 12370      # 开启本地 rtraw→ESD 重建
#   （RECON_SLICE/RECON_EVTMAX 控规模；默认 1 文件×100 事例=冒烟级）
# AmC 输入数据（RUN10110+本底10100）预置于 calibsel/input/amc_data/；换 run 时
# 按 calibsel/PROVENANCE.amc.md §3 从 lustrefs 拉取对应 Finalcorrection npz
```

输出：

```text
output/<YYYYmmdd_HHMMSS>/
├── recon/        # 【仅 RECON_IMPL 开启】results/(esd/RUN{N}/, esd_lists/) + 审计
├── calibsel/     # results/(npz_raw, npz_corrected, selection_npz, timestamps)
│                # figures/  cuts/（挑选条件）  logs/  code/（代码快照）
│                # run_log.{md,json}（含 audit）  config_snapshot.json
├── calibsel_amc/ # AmC 支线：results/RUN{N}/(correlation_result_RUN{N}.npz,
│                #   FV/关联 pdf)  timestamps/  code/  run_log.{md,json}
├── peakfit/     # results/(RUN{N}_{源}.npz, RUN{N}_{nH,nC,AmC}.npz)  figures/
│                # enl_style_resolution.*  code/  run_log.{md,json}  config_snapshot.json
├── peakfit_amc/ # AmC 三峰拟合单独留档（结果 npz 汇入 peakfit/results）
└── nlfit/       # results/(gamma_AllPhase.dat, bestFit_*.dat, nl_curves.tsv,
                 #          Etrue_from_Erec_lookup.npz/csv)
                 # figures/(stage5_gamma_peaks, stage6_nl_curves,
                 #          stage7_inversion, dybmodel/)
                 # code/  run_log.{md,json}  config_snapshot.json
```

peakfit 自动读取**同批** calibsel 的 `results/selection_npz`，nlfit 自动读取
**同批** peakfit 的 `results/`——全链无需手动衔接。

单项目独立运行：

```bash
cd calibsel && bash run_pipeline.sh 12370 --out-dir <目录>
cd peakfit && .venv/bin/python pipeline/run_fit_all.py \
    --input-dir <selection_npz目录> --out-dir <输出目录>
cd calibsel && .venv/bin/python pipeline/run_amcsel_all.py --run 10110 \
    [--input-dir <Finalcorrection npz目录>] --out-dir <输出目录>   # AmC 支线
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

- 数据处理与溯源：`calibsel/README.md`、`calibsel/PROVENANCE.md`
- 本地重建（rtraw→ESD）与溯源：`recon/README.md`、`recon/PROVENANCE.md`
- AmC 支线挑选与溯源：`calibsel/README.amc.md`、`calibsel/PROVENANCE.amc.md`
- 拟合设计与日志规范：`peakfit/README.md`、`peakfit/DESIGN_REPORT.md`
- 非线性拟合与外部数据契约：`nlfit/README.md`、`nlfit/external_inputs/MANIFEST.json`
- 使用手册：各模块 `skills/`（环境/配置/运行/排障/审计）

## 相关文档（飞书）

- [MiniESD2npz 流程报告](https://xcnjvifx7evw.feishu.cn/docx/COu3d06GOogbzgxijWccuQJXn2N)
- [刻度峰位拟合](https://xcnjvifx7evw.feishu.cn/docx/Mxqmdu2BeooCZexGvRncDsgin6g)
