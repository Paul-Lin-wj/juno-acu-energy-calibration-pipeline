---
name: nlfit-stage
description: nlfit 模块 stage skill——非线性全局拟合（Stage 4b/5/6/7）的项目背景、怎么跑、每 stage 的物理含义、产物与图怎么读。进入 nlfit/ 深潜、跑 nlfit、解读 gamma 表/NL 曲线/E_true 查询表时用这个。
---

# Skill: nlfit — 非线性全局拟合（链路第 4 段）

> 指导级入口见 `.claude/skills/pipeline-suite/SKILL.md`；设计文档
> `nlfit/README.md`；红线（什么不能动）见仓库根 `CLAUDE.md`。

## 1. 背景：这一段在测什么物理

液体闪烁体探测器里，**1 pe/MeV 转换不是常数**：Cherenkov 光贡献、
闪烁体猝灭（Birks）、电子学非线性，使 E_rec/E_true 随能量弯曲——
JUNO 要 sub-percent 能量精度，这条非线性曲线必须校出来。

链路前两段给出的是 7 个已知能量点的 (E_true, E_rec)：

| 顺序 | 峰 | E_true (MeV) | 来源 |
|---|---|---|---|
| 1 | Cs137 | 0.6617 | peakfit |
| 2 | Mn54 | 0.835 | peakfit |
| 3 | Ge68 | 1.022（e⁺湮灭对） | peakfit |
| 4 | nH | 2.2233 | AmC 关联对 |
| 5 | Co60 | 2.506（级联和） | peakfit |
| 6 | nC | 4.95 | AmC |
| 7 | O16 | 6.129 | AmC |

（7 峰顺序是 dybmodel C++ `LoadData` 写死的；K40 是连续谱不是峰，不进表。）

nlfit 做三件事：**聚合** 7 峰（0.66→6.13 MeV 跨一个量级）→
**dybmodel C++ 全局拟合**（把 7 个点 + 连续谱同位素 B12/C10/C11 +
Michel 电子谱放进统一 dyb 物理模型同时拟合非线性参数）→
**反演**出查询表 E_true = f(E_rec)（给物理分析用——测量的是 E_rec，
要的是 E_true）。

## 2. 怎么跑

```bash
# 通常不单独跑——顶层 run_pipeline.sh 第 [5/6] 段自动调，输入吃
#   --fitter-results <OUT>/peakfit/results
cd nlfit && bash run_pipeline.sh \
    --fitter-results <OUT>/peakfit/results --out-dir <OUT>/nlfit [--phase N]

# 单独干跑（不进容器，只 4b+5；排障用）
bash run_pipeline.sh ... --skip-dybmodel
# 行为锁复核（dybmodel 与历史 bestFit 对比；改容器/环境后必跑）
bash run_pipeline.sh ... --validate-ref
```

环境：`.venv`（numpy/scipy/matplotlib）+ Stage 6 需
`DYBMODEL_DATA`（当前 /scratchfs2/juno/lidian/dybmodel_data）+
官方容器 `/cvmfs/container.ihep.ac.cn/bin/hep_container exec SL6 -g juno`
（登录/计算节点都验证过可用）。

## 3. 逐 stage：含义 / 产物 / 图怎么读

### Stage 4b — 外部数据契约校验
**含义**：连续谱输入（`Isotope_data_*.root`，同事交付）与过渡期历史值
不是本链路产的，属外部依赖——开跑前 sha256 对照 `external_inputs/
MANIFEST.json`，防"输入悄悄变了结果就变了"。**产物**：校验记录进
run_log，无图。**读法**：run_log 里 contract 校验 FAIL 就停下查输入，
不要带病进 5/6。

### Stage 5 — 7 峰聚合
**含义**：γ 源 μ（provider=fitter）+ AmC 三峰 μ（provider=amc）→
每峰一个加权均值（分相模式：该 phase 各中心 run μ 的方差倒数加权；
err 下限 MU_ERR_FLOOR=0.005，防统计误差过小被过度加权）。缺峰：分相
模式**剔除**+告警，AllPhase 模式钉历史值（字节级保持旧行为）。
**产物**：`gamma_AllPhase.dat` 或 `gamma_Phase{N}.dat`（7 行"E μ_err"，
**这就是 dybmodel 的输入卡**）、`gamma_*.dat.provenance.json`（每行
来自哪些 run、加权细节）、`meanEscaleEres_perPhase_CDcenter.dat`
（分相聚合明细，n 列=该源用了几个 run）。
**图 `stage5_gamma_peaks.png`**：上panel E_rec/E_true vs E_true——
× 历史生产值、● 本链路实测、□ 钉值点；下panel 相对历史偏差 %。
**读法**：点离 × 的距离=复现精度；曲线形状（低能塌、~2 MeV 处峰、
高能回落）是 LS 非线性的标准形态，物理上应当平滑，点间跳变通常指示
某峰拟合有问题而非物理。

### Stage 6 — dybmodel 全局拟合
**含义**：原版 C++ fitter（二进制 sha256 钉死）在官方 SL6 容器
（ROOT 5.34 环境）里跑，**零改码**：符号链接农场沙箱把 gamma 表 +
该 phase 的 isotope root 物化到 C++ 写死的读入路径——喂文件而非改
代码。分相时 `Isotope_data_Phase{N}_*.root` 物化为 AllPhase 文件名。
**产物**：`bestFit_*.dat`（拟合参数+误差）、`chi2_*.dat`、
`matrix_*.dat`（协方差）、`curves_*.root`、`nl_curves.tsv`。
**图 `stage6_nl_curves.png`**：拟合出的 e⁻/e⁺/γ 三条 NL 曲线 +
7 峰数据点落点。**读法**：χ²（console/run_log）看拟合质量；
数据点应贴着 γ 曲线；三曲线在高能区趋同、低能区分裂是模型预期。
分相模式下四条 γ 曲线（P1-P4）叠起来看漂移=探测器状态的能标演化。

### Stage 7 — E_true = f(E_rec) 反演
**含义**：NL 曲线是 E_rec/E_true vs E_true，物理分析要反着查——
给 E_rec 求 E_true。纯 Python 数值反演（e⁻/e⁺/γ 三条），带单调性
校验和往返误差检查（≤2e-5）。
**产物**：`Etrue_from_Erec_lookup.npz/.csv`（插值查询表，**下游物理
分析直接消费的最终交付物**）。
**图 `stage7_inversion.png`**：反演曲线 + 往返误差。**读法**：误差
panel 应全程 ~1e-5 量级平线，出现尖峰=数值问题，不是物理。

## 4. 跑完怎么核对

1. run_log audit passed；gamma 表行数=7（分相模式可能少，看告警）
2. 与生产表对比（口径！）：nC 生产钉 5.08140，本链默认实测——差
   ~0.5% 是口径不是 bug（`--nc-pin` 对齐）；P1 表 8 行含 K40，跳过
   K40 行再比；P1 的 Cs137/Mn54/Co60 来自试运行周、生产口径不同
   （详见 pipeline-suite §5，未决、勿自行"修"）
3. Stage 7 单调性/往返误差通过

## 5. 红线（本模块特有）

- `MU_ERR_FLOOR`、钉值逻辑、加权方式、7 峰顺序：⛔ 用户发话
- `config/paths.py::ISOTOPE_ROOT_BY_PHASE` 加映射：✅ 自主（加新
  phase 的唯一代码改动点，数据驱动设计如此）
- pinned fitter 二进制、`dybmodel/` C++ 源：⛔（行为锁对象，
  `--validate-ref` 可随时复核）
