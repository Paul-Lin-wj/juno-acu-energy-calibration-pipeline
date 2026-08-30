---
name: recon-stage
description: recon 模块 stage skill——可选的 rtraw→ESD 本地重建段（Stage −1）背景、怎么跑、产物与边界（默认关、与生产 ESD 非逐位一致）。考虑开本地重建、排障 recon、或被问"为什么不直接用官方 ESD"时读这个。
---

# Skill: recon — rtraw→ESD 本地重建（链路可选第 0 段）

> 指导级入口：`.claude/skills/pipeline-suite/SKILL.md`；细节
> `recon/README.md` + `recon/PROVENANCE.md`；红线见仓库根 `CLAUDE.md`。

## 1. 背景：为什么存在、为什么默认关

链路的能量输入是**顶点/能量重建后的 ESD**。默认直接读生产 ReProd26B
ESD（`calibsel` 默认 from-edm 模式的上游）——生产重建是既定事实源。

本模块回答另一个问题："如果自己从 DAQ 原始 rtraw 重建，能标结论变
多少？" 它是**纯编排包装**（零算法代码）：调官方 CVMFS J26.1.1
`tut_rtraw2rec` 链（waverec 波形刻度 → OEC → mixedphase → jvertex →
OMILREC 顶点/能量）。`--impl omilrecv2|baseline` 选 OMILREC 实现
（v2 overlay ~8× 提速，与基线差 ≤55 keV/150 mm，**非逐位一致**）。

**默认关闭**的原因：⚠️ 官方冻结 tag 是 26A，生产 ESD 是 26B——口径
有差异待量化，所以"用本地重建替代生产 ESD 出正式结果"属于 ⛔ 请示
事项（当前用途是验证/研究，不是替代）。

## 2. 怎么跑

```bash
cd recon
bash run_pipeline.sh                       # 冒烟：10110, 1 rtraw × 100 事例
bash run_pipeline.sh 10110 --slice 297 --evtmax -1   # 全量（10110 有 297 个 rtraw）
bash run_pipeline.sh 10110 --impl baseline  # 官方基线 OMILREC（"官方答案"）

# 套件联合（顶层 driver 默认关）：
RECON_IMPL=omilrecv2 bash ../run_pipeline.sh 12370
```

- 无需 venv（编排脚本纯标准库；重建在 wrapper 里用 CVMFS python 跑）
- 需要：CVMFS JUNOSW 可达 + EOS xrootd（读 rtraw 原始档）
- `RECON_SLICE / RECON_EVTMAX` 是冒烟/全量旋钮（✅ 自主，验证用途）

## 3. 产物与衔接

```
output/<ts>/
├── results/esd/RUN<N>/recon_RUN<N>.root   # ESD（Event/CdVertexRecOMILREC）
├── results/esd_lists/esd_list_<N>.txt     # ★ 衔接清单
└── logs/ _work/ code/ config_snapshot.json run_log.md/.json
```

衔接是**存在性驱动**：顶层 driver 里 `RECON_IMPL` 已设且
`$OUT/recon/results/esd_lists/` 存在时，calibsel 前段自动加
`--full-esd --esd-list-dir ...` 吃本地 ESD（本底 run 也会被一并重建，
映射表驱动）；否则一切照旧用生产路径。**没有任何"半开"状态**——
要么整批走本地重建，要么整批走生产。

## 4. 怎么读结果

- 本模块**没有物理 QA 图**——它的产物 ESD 是给下游的中间件，质量由
  下游（calibsel QA 图、peakfit χ²）间接体现
- 判断"本地重建 vs 生产 ESD 影响多大"的正确做法：同一 run 两种来源
  各跑一遍完整链路，比 gamma 表逐峰差异（对比结论汇报，勿自行调整）
- 排障先看 `logs/`（junosw wrapper 原始输出），常见问题：CVMFS 未挂、
  xrootd 读 EOS 超时、OMILRECV2 overlay 路径不在

## 5. 红线（本模块特有）

- flag 集（`recon/config/paths.py` 冻结的 junosw 参数）：⛔（PROVENANCE
  锁定，改了就不再是"官方链的忠实编排"）
- slice/evtmax、提交参数：✅ 自主
- **把本地重建 ESD 用于正式刻度结果**：⛔ 请示（26A vs 26B 口径未对齐）
