# Skill: runcheck — 启动链路前的 run 挑选检查

## Description

自动化链路的唯一输入是 **run 号**；"哪些 run 可用、可不可信"是启动前的
人的决策。本 skill 说明：run 信息的事实源在哪、两套 DQ runlist 各覆盖
什么、以及如何用本目录的工具做启动前检查。之后的 agent 在替用户挑 run、
诊断"这个 run 为什么没进生产"或"该不该用这个 run"时用这个 skill。

---

## 1. Run 信息的事实源（在哪）

| 数据 | 位置 | 内容 |
|---|---|---|
| 刻度 run 事实表 | `runcheck/data/CalibRUN_from_file.csv` | RUN / Date / X,Y,Z[m] / Source / R[m]，全 ACU 刻度 run（含非中心 z 扫描） |
| 源→区间→本底映射 | `runcheck/data/calib_to_analyze.txt` | 每源刻度 run 区间 + 对应本底 run（Stage 3 本底扣除用） |
| phase 区间表 | `calibsel/input/correction/data/ValProd26BPhase.csv` | P1 9737-11045 / P2 11049-12135 / P3 12136-13463 / P4 13466-15250 |
| **物理** good run list | `runcheck/data/goodrunlist_v<ver>/<phase>/physics_good.txt` | DQ 组认证的物理分析 good run（当前 v5.0.5，2564 个） |
| **刻度** good run list | `runcheck/data/calib_runlist/<phase>_calibration_good.txt` | DQ 组认证的刻度 good run（phase1-4b 共 948 个） |
| 刻度 rtraw/kup_esd 逐 run 清单 | `runcheck/data/calib_runlist/{rtraw,kup_esd}_runnames/<phase>.txt` | 进了重建 / 已重建 ESD 的 run 名单 |

EOS 原始位置（刷新用）：

- 物理：`/eos/juno/groups/DataQuality/ReProd26B/Physics/<phase>/goodrunlist_vX.Y.Z/`
- 刻度：`/eos/juno/groups/DataQuality/ReProd26B/Calibration/reprod_runlist/<phase>/`
  （`calibration_good.txt` + `rtraw_list/run_*.txt` + `kup_esd_list/run_*.txt`）

## 2. 两套 runlist 意味着什么（关键口径，2026-08-30 核对）

**刻度 run 和物理 run 是两棵树、两套认证，互不覆盖：**

1. **刻度源 run 不在物理 good list 里——结构性如此，不是被剔了。**
   `physics_good.txt` 只收物理取数 run；刻度 run 有自己的
   `calibration_good.txt`。看到刻度 run "不在 goodrunlist" 不要 alarmed。
2. **prephase1 没有单独的刻度 good 文件**：该时期（run<9737，2025-08
   试运行周）的 `rtraw_list/` 全集（160 个）即事实清单。
3. **本底 run 是物理取数 run**（紧邻刻度 run 采集，当本底扣除用），
   它的 DQ 状态查**物理** good list，不在刻度 list 里。
4. **物理 list 的版本变更不自动作用于刻度侧**：v5.0.5 因高氡剔除物理
   run 14356–14706，但刻度 good list **未剔**该区间的刻度 run（Ge68
   14417、AmC 14463 仍 good）——生产 P4 口径也未剔。复刻时维持不剔。
5. `calibration_good`（948）里约 603 个 run 不在本项目刻度事实表中——
   那是其它类型刻度（激光/RSM/电子学等），与 ACU 源刻度无关。

**已核对结论**：本项目 44 个中心 run（P1–P4 的 39 个在 calibration_good；
pre-P1 的 5 个在 prephase1 rtraw 全集）全部通过刻度 DQ。

## 3. 怎么做启动前检查（agent 操作流程）

1. **可用性**：看 `runcheck/run_date_map.png`（源 × 日期，phase 带，
   实心点 = 中心 run）——确认目标 phase 各源是否有中心 run。
   - 注意 P1 区间内只有 Ge68 + AmC；Cs137/Mn54/Co60/K40 只存在于
     pre-P1 试运行周（生产口径：折叠进 P1 表）。
2. **DQ**：把候选 run 对照第 1 节的 list——刻度 run 查 calibration_good
   （pre-P1 查 prephase1 rtraw），本底 run 查 physics_good。
3. **交给链路**：把选好的 run 号作为唯一输入启动
   `bash run_pipeline.sh <run...>`（phase 批量复刻用 `run_phase_all.sh`）。

## 4. 全量 run 信息一览

`runcheck/data/run_inventory.csv`（生成：`python3 runcheck/tools/make_run_inventory.py`）
— rtraw 刻度全集（1108）∪ 物理 good（2564）∪ 刻度事实表（398）= 3672 行，
每 run 一行：

| 列 | 含义 |
|---|---|
| run, phase, date, source, x_m/y_m/z_m | 事实表信息（无信息则空） |
| is_centre | \|z\| ≤ 0.5 m（能量刻度中心 run） |
| in_calib_table | 是否在 ACU 刻度事实表（否 = 激光/RSM 等其它刻度类型） |
| calib_good / prephase1_rtraw | 刻度 DQ 状态 |
| physics_good | 物理 DQ 状态（本底 run / 物理取数参考） |
| in_kup_esd | 是否已有重建 ESD（链路 from-edm 模式的输入存在性） |

用表格而非图：1108 run × 8 属性的信息量图装不下（会退化成色块噪声），
表可以排序/过滤/逐 run grep，也方便 agent 程序化消费。

## 5. 边界（与链路的关系）

- 本目录**不属于链路**：不进任何 stage 的输入/输出，图和表都是给人
  （和 agent）做启动前决策用的。
- 链路模块只读引用 `runcheck/data/` 下的事实表；calibsel 冻结 src 经
  `calibsel/calib_run_info → runcheck/data` 符号链接读取（零改动）。
