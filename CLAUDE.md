# CLAUDE.md — juno-acu-energy-calibration-pipeline

JUNO ACU 刻度能区自动化链路：calibsel（刻度事例挑选）→ peakfit（峰位拟合）
→ nlfit（dybmodel 全局非线性拟合）。本仓库由自动化 agent 维护运行。

## 硬红线：影响物理结果的改动必须用户发话（DEADLOCK）

**Agent 在本项目里只负责跑链路，不是物理负责人。** 以下类别的改动都是
**可以动的，但必须用户发话**——没有用户对本项改动的明确指示（明确说
"把 X 改成 Y"）绝不执行：

1. **任何数值修正/缩放因子**：绝对能标（absolute_scale）、phase scale、
   能量加权、误差地板、钉值（如 nC 5.08140）——不新增、不删除、不改值。
   "复现偏差 → 推测某因子 → 就补上"是明令禁止的路径：偏差要汇报，不要修。
2. **src/ 与 input/correction/ 下的算法文件**：审计冻结（逐位一致性保证
   依赖它们，见 calibsel/README.md"数值保证"）。发现疑似 bug 只报告。
3. **挑选 cut、拟合区间、本底处理、run 选择口径**（中心 run 定义、
   pre-P1 折叠等）：这些本来就允许调整，但每次调整都要用户先发话。
4. **dybmodel C++ 与 pinned fitter 二进制**：行为锁（byte-identical
   bestFit）依赖其不变。

例外（无需逐次请示的日常运维）：venv/依赖安装、调度脚本、日志留档、
画图工具、集群作业提交参数（内存/队列）等不影响物理数值的基础设施。

**判断准则：拿不准某改动是否影响物理结果 → 当作影响，汇报待批。**
发现复现偏差时的正确动作：定位（数据/口径/代码哪一层）→ 汇报证据
→ 提出可选处理方案 → **用户拍板后才动**。

## 链路速览

- `run_pipeline.sh` — 顶层串行驱动；run 号按 `calib_to_analyze.txt`
  自动分流（Am/Cf → AmC 支线，其余 → γ 支线）
- `run_phase_all.sh` — phase 复刻驱动（每 phase 解析中心 run → 注入
  PEAKFIT_RUNS/NLFIT_PHASE/OUT_ROOT）
- `TMP/hepsub/submit_phases.sh` — hep_sub 集群提交（每 phase 一个作业，
  `-m 8000` 必带：Stage 1 整 run numpy 常驻会打爆默认 2.5G cgroup）
- 各模块：`calibsel/`（γ: Stage1 EDM→NPZ → Stage2 26B 修正 → Stage3
  挑选 → Stage4 QA；AmC: 前段共用，到 npz_corrected 分流 → 关联对挑选）、
  `peakfit/`（MC 模板卷积拟合）、`nlfit/`（聚合 → dybmodel 拟合 →
  E_true=f(E_rec) 反演）
- 环境：lxlogin 节点 + `/cvmfs/container.ihep.ac.cn/bin/hep_container
  exec SL6 -g juno`（零拷贝用官方容器）；`DYBMODEL_DATA` 在
  /scratchfs2/juno/lidian/dybmodel_data（lustrefs 有 30 万文件数配额）
- 每次运行自动留档：run_log.{md,json} + cuts/ + code/ 快照 + 审计；
  结果与生产表对比结论写进汇报，不在代码里"对齐"

## 已知非 bug（勿"修"）

- O16 拟合 HESSE 常失败（参数贴边）→ err=0，下游 MU_ERR_FLOOR=0.005
  兜底——生产同款行为
- nC 复现偏差 ~0.5-1.3%：生产表钉 5.08140，链路默认不钉（`NC_PIN=1`
  可对齐口径，这是用户已批的例外）
- P1 表的 Cs137/Mn54/Co60 行偏差 ~0.7%：源于生产对 pre-P1 试运行周
  （2025-08-24~25，run<9737）的口径，2026-08-30 已汇报，**待用户定夺**
