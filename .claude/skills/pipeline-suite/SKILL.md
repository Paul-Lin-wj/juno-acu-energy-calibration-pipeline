---
name: pipeline-suite
description: 指导级 skill——JUNO ACU 刻度自动化链路（calibsel→peakfit→nlfit）怎么跑、跑的规范、红线与汇报纪律。处理本仓库任何"跑链路 / 跑 phase / 出 gamma 表 / 排错 / 看结果"请求前必读；各 stage 细节再进对应子 skill。
---

# JUNO ACU 刻度链路 · 指导级操作规程

> 本 skill 管"整体怎么跑、什么能自己动、什么必须请示"。
> **stage 深潜索引**（背景/怎么跑/含义/产物/图怎么读，按需进）：

| 环节 | stage skill | 补充材料 |
|---|---|---|
| 启动前挑 run（非链内） | `runcheck/SKILL.md` | `runcheck/README.md`、run_date_map.png |
| recon（可选重建） | `.claude/skills/recon-stage/SKILL.md` | `recon/README.md`、`recon/PROVENANCE.md` |
| calibsel（挑选） | `calibsel/skills/01_project_overview.md` 起步 | 同目录 10 篇（QA 图看 08、cut 与留档看 07、审计看 10） |
| calibsel AmC 支线 | `calibsel/README.amc.md`、`calibsel/PROVENANCE.amc.md` | |
| peakfit（峰位拟合） | `peakfit/skills/`（10 篇，从 project_overview 起步） | 同目录 10 篇（结果解读看 09、ENL 图与 Z 扫描看 08） |
| nlfit（非线性拟合） | `.claude/skills/nlfit-stage/SKILL.md` | `nlfit/README.md`（设计文档） |

> 新 agent 上手路径：读本篇 §0-§2 → 跑一个 phase 冒烟（§2）→ 对照
> §3 核对产物 → 需要动哪个 stage 再进上表对应 skill。项目全链覆盖图
> 在顶层 `README.md`。

## 0. 角色定位（先读这个）

**你是跑自动化链路的 agent，不是物理负责人。** 链路本身已把物理口径
固定在代码/数据里（26B 修正、cut 定义、拟合区间、聚合口径、pinned
fitter）。你的职责是：正确执行、如实留档、发现异常**汇报**。
红线全文见仓库根 `CLAUDE.md` —— 摘要：

- **能自主**：运维类（venv/依赖、调度接线、集群作业参数、画图、日志
  机制、不触数值流的 bug 修复、验证性重跑）
- **须用户发话**：任何流进 gamma 表/物理结论的数字——scale/钉值/误差
  地板的增删改、`src/` 与 `input/correction/` 算法、cut、拟合区间、
  本底处理、run 选择口径（中心 run 定义、pre-P1 折叠）、fitter 二进制
- **明令禁止的路径**：复现偏差 → 推测某因子 → 自己补上。偏差只定位、
  只汇报、只列方案，等拍板
- 拿不准是否影响物理 → 按影响处理

## 1. 链路一图流

```
run_pipeline.sh <runs...>          # γ+AmC run 号自动分流（calib_to_analyze.txt）
├─ [0/6] recon        （RECON_IMPL 才开；默认用生产 ESD，跳过）
├─ [1/6] calibsel 前段  EDM→NPZ→26B 修正（源无关）
│        ├─ γ run  → Stage 3 挑选 → Stage 4 QA → SelectionResult.npz
│        └─ AmC run → 到 npz_corrected 收尾（is_amc_source: Am/Cf 标签）
├─ [2/6] calibsel AmC  逐 run 关联对 → correlation_result_RUN{N}.npz
├─ [3/6] peakfit γ     MC 模板卷积拟合（--runs 限定 phase 中心 run）
├─ [4/6] peakfit AmC   逐 run 三峰拟合 → npz 汇入 peakfit/results/
├─ [5/6] nlfit         契约校验→聚合→dybmodel（官方 hep_container）→反演
└─ [5b/6] 图 PNG↔PDF 配对
```

phase 复刻：`run_phase_all.sh [N...]` 解析该 phase 中心 run（与
nlfit `select_phase_runs` 同口径），注入 `PEAKFIT_RUNS/NLFIT_PHASE/OUT_ROOT`
后调顶层脚本；每 phase 一棵完整留档树。

## 2. 标准跑法

### 单批（登录节点，冒烟/小批）
```bash
bash run_pipeline.sh 12370 10110        # 显式 run（γ + AmC 自动路由）
# 前提：calibsel/.venv peakfit/.venv nlfit/.venv 就绪；默认 from-edm
```

### 全 phase 复刻（集群，推荐）
```bash
bash TMP/hepsub/submit_phases.sh        # 4 作业并行 → output/<ROOT_TS>/phase{N}/
bash TMP/hepsub/submit_phases.sh 2      # 只跑指定 phase
NC_PIN=1 ...                            # nC 钉 5.08140（已批例外，默认不钉）
# NL 曲线 68% C.L. 误差带采样（拒绝采样慢，只能上集群；见 submit_clband.sh 头注）
bash TMP/hepsub/submit_clband.sh 1 output/<ts>/phase1 100
```
- **`-m 8000` 必带**：Stage 1 整 run numpy 常驻（本底 run 440 万事例
  ≈2.5 GB），默认 2.5 GB cgroup 会 held（8368979 实测）
- 节点已验证同构（AlmaLinux9/py3.9.25/lustrefs+scratchfs2+cvmfs 挂载/
  hep_container exec 可用——TMP/hepsub/probe_node.out）
- 时长参考：P2 ~33 min、P1/P3 ~50 min、P4 ~55 min（AmC run 数主导）；
  clband 采样 ~4 min/条 → NITR=100 约 7-12 h，**只交集群勿在登录节点跑**

### 常用变量
`DYBMODEL_DATA`（scratchfs2 上）、`NLFIT_FLAGS`（如 --skip-dybmodel 干跑）、
`SUITE_FLAGS`（透传 calibsel）、`OUT_ROOT`、`ROOT_TS`（并行作业共树）、
`DYB_CLBAND_FITTER`+`CL_CONTOUR_NITR`（误差带采样 opt-in，默认关= pinned
二进制原行为）

## 2b. 算力纪律（集群 vs 登录节点）

**大任务交 hep_sub 节点作业；登录节点只做快速分析**（画图、表格对比、
<10 min 的单段验证）。判据——任一成立即上集群：

- 预计 >30 min（全 phase 链路、dybmodel 拟合 7 min、CL 采样 4 min/条）
- 整 run numpy 常驻 >2 GB（Stage 1，`-m 8000` 必带）
- 多 phase 并行（每 phase 一个作业共树）

作业模板：`TMP/hepsub/submit_phases.sh`（全链路）、`submit_clband.sh`
（误差带采样）。登录节点挂多小时后台任务**不许**——会话退出连杀子进程
（8404199 前身实测被杀，且占共用登录资源）。

**交完作业必挂监视器**（CronCreate 定时，30 min 间隔足够）：
1. `hep_q -u lidian` 查状态
2. 在跑：看输出树关键文件的 mtime/大小增长（如 errors_*.root 逐条涨）
   → 汇报进度，继续等
3. 完成：查 run_log audit + 与基线逐字节核对（行为锁），然后走画图/汇报
4. held/失败：读作业 `.out.<jobid>.0` 与模块 log 定位，汇报勿自行重交

## 3. 跑的规范（每次运行都要守住）

1. **别绕留档**：永远走 run_pipeline.sh / run_phase_all.sh 入口——
   suite log、模块 run_log、cuts、code/ 快照、结束审计自动生成；
   手工单跑某脚本仅限排障，且结论要说明"未经完整留档"
2. **完成 ≠ 通过**：收尾必查 `suite_run_log.md`——exit 0 且各模块
   audit passed=True 才算数；audit-failed 的产物不用于对比/汇报
3. **对比口径**：与生产 gamma 表对比时，nC 记得注明是否 NC_PIN（生产
   钉 5.08140，默认不钉会差 ~0.5%）；P1 表是 8 行（含 K40）且试运行周
   口径不同（见 §5 已知事项）
4. **产物只读**：output/ 树是审计快照，不手改；重跑 = 新时间戳树
5. **排障顺序**：console.log 尾部 → suite_run_log 的 FAILED stage →
   模块 run_log.json 的 errors[] → traceback.log；修的若属运维类
   （调度/依赖/内存）直接修，若触及数值流——停下汇报
6. **删文件前确认**：output/ 之外不乱删；删 output 树要向用户说明

## 4. 判断表（能不能自己动）

| 想动的东西 | 判定 |
|---|---|
| venv 缺包、requirements 补依赖 | ✅ 自主 |
| hep_sub 内存/队列/walltime、探针 | ✅ 自主 |
| 驱动脚本接线（pipefail/tee/共树/循环 bug） | ✅ 自主 |
| 画图/对比表工具（只读结果） | ✅ 自主 |
| 崩溃修复（不改数值流，如 summary tuple-key） | ✅ 自主 |
| 哪个 phase 先跑/重跑某 stage | ✅ 自主（验证用途） |
| absolute_scale、误差地板、钉值 | ⛔ 请示 |
| src/、input/correction/ 算法文件 | ⛔ 请示（审计冻结） |
| cut、拟合区间、本底处理 | ⛔ 请示（可调，但要发话） |
| run 选择口径（中心 run/pre-P1 折叠/K40 跳过） | ⛔ 请示 |
| peakfit SOURCES 默认集、固定参数 a/b/c | ⛔ 请示 |
| pinned fitter 二进制、历史 gamma 表、连续谱 root | ⛔ 请示 |
| 换 EDM 数据源、本地重建出正式结果 | ⛔ 请示 |

## 5. 已知事项（勿当 bug 修）

- **O16 HESSE 常失败**（参数贴边）→ err=0，下游 MU_ERR_FLOOR=0.005
  兜底——生产同款
- **nC 偏差 ~0.5-1.3%**：生产钉 5.08140 vs 链路默认不钉；NC_PIN=1 对齐
- **P1 表 Cs137/Mn54/Co60 偏 ~0.7%**：P1 区间内无这些源，只能用
  2025-08-24~25 试运行周 run（date-vs-run 图：calibsel/tools/
  run_date_map.png）；生产对 pre-P1 的口径与链路不同——2026-08-30
  已汇报，**待用户定夺，链路侧不动**
- P1 表 8 行（含 K40 1.426 MeV 行），本链 7 峰表对齐时跳过 K40 行

## 6. 汇报模板（跑完 phase 批次）

```
Phase N 完成：<output 树路径>
- 时长 / 各 stage 表（suite_run_log）
- gamma_Phase{N}.dat vs 生产：逐峰相对偏差（注明 NC_PIN 状态）
- 异常：HESSE 告警数、audit 结果、跳过的 run
- 结论：复现是否达标；不达标的定位到哪一层（数据/口径/代码）
```
