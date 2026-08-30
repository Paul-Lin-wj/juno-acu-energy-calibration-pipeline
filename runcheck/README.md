# runcheck — 启动链路前的 run 挑选检查（用户级，不属于链路）

自动化链路的输入只有一个：**run 号**（`bash run_pipeline.sh 12370 10110`）。
"这些 run 怎么选出来"是人的决策，发生在链路启动**之前**——本目录服务于此。

## 内容

### 图

- `run_date_map.png / .pdf` — 各刻度源中心 run（|z| ≤ 0.5 m）随时间的可用性
  总览（源 × 日期，phase 时间带）：挑 run 时先看这张图。
- `tools/make_run_date_map.py` — 上图的生成脚本（只读事实源表，不改链路）。

### 事实源表（data/）

| 文件 | 内容 | 来源 |
|---|---|---|
| `CalibRUN_from_file.csv` | 刻度 run 事实表（RUN/Date/位置/Source） | 生产拷贝（md5 冻结） |
| `calib_to_analyze.txt` | 源→run 区间→本底 run 映射 | 生产拷贝（md5 冻结） |
| `goodrunlist_v5.0.5/<phase>/` | **物理分析** good run list（含 physics_good.txt） | EOS `DataQuality/ReProd26B/Physics/` |
| `calib_runlist/` | **刻度** good run list + rtraw/kup_esd 逐 run 清单 | EOS `DataQuality/ReProd26B/Calibration/reprod_runlist/` |
| `run_inventory.csv` | 上述全集并集单表（3672 行，DQ + ESD 状态） | `tools/make_run_inventory.py` 生成 |

### 两套 DQ 清单的分工（2026-08-30 核对）

- **物理 run** 用 `goodrunlist_v5.0.5`（v5.0.5 相对 v5.0.4b 剔除高氡区
  14356–14706）。刻度源 run **不在**此清单——结构性如此，刻度 run 有自己的
  DQ 口径，两套清单按 run 类型互不覆盖。
- **刻度 run** 用 `calib_runlist/{phase}/calibration_good.txt`（phase1–4b，
  共 948 个）。prephase1 没有单独的 good 文件，其 `rtraw_list/` 逐 run
  清单（160 个）即该时期刻度 run 全集。
- **本底 run**（`calib_to_analyze.txt` 第三列，紧邻刻度 run 的物理取数）
  不在刻度 good list（它不是刻度 run）；其 DQ 状态查物理 good list。
- 已核对：44 个中心 run 中，P1–P4 的 39 个全部在 `calibration_good`；
  pre-P1 的 5 个（9541/9591/9600/9609/9624）在 prephase1 rtraw 全集内。

## Agent 参考

runlist 位置、两套 DQ 口径、启动前检查流程见 **[SKILL.md](SKILL.md)**
（之后的 agent 替用户挑 run / 判 DQ 时先读它）。

## 与链路的关系（并列，非链内）

- 链路模块（calibsel 等）按只读方式引用 `runcheck/data/` 下的事实表；
  calibsel 的审计冻结代码经 `calibsel/calib_run_info → runcheck/data`
  符号链接读取（冻结 src 零改动，逐位行为不变）。
- 本目录不进任何 stage 的输入/输出；这里的图不是链路中间产物，是给人
  做启动前检查用的。

## 重新生成图

```bash
calibsel/.venv/bin/python runcheck/tools/make_run_date_map.py
```

## 刷新 DQ 清单（新版本发布时）

```bash
# 物理：/eos/juno/groups/DataQuality/ReProd26B/Physics/<phase>/goodrunlist_vX.Y.Z/
# 刻度：/eos/juno/groups/DataQuality/ReProd26B/Calibration/reprod_runlist/<phase>/
# 例（v5.0.6 发布后）：
for ph in phase1 phase2 phase3 phase4 phase4b; do
  xrdcp -f "root://junoeos01.ihep.ac.cn//eos/juno/groups/DataQuality/ReProd26B/Physics/$ph/goodrunlist_v5.0.6/physics_good.txt" \
        "runcheck/data/goodrunlist_v5.0.6/$ph/physics_good.txt"
done
```

绘制规范：academic-research-skills / statistical_visualization_standards.md
（Tol 色盲安全板、颜色×形状双编码、无 chartjunk、300 dpi）。
