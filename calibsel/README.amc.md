# calibsel AmC 支线 — AmC（中子源）关联对挑选（Stage 3c）

JUNO ACU 能量刻度链中 **(prompt, delayed) 关联对挑选** 模块：AmC（及 Co60/Cf252
等关联源）的 ¹³C(α,n)¹⁶O* 事例中，prompt 是 O16 退激发 6.129 MeV γ，
delayed 是中子俘获 —— n-H 2.2233 MeV / n-¹²C 4.945 MeV。本模块产出这三个峰
的能量数组，供 `fitter/pipeline/run_amc_fit_all.py` 拟合，再汇入
`nlfit` 的非线性拟合（7 峰 gamma 表的 nH/nC/O16 三行）。

**原作者**：Shubing Liu <liusb@ihep.ac.cn>（`correlate_selection`，2025-01-11 起）。
本支线为其代码的原样并入（仅两行 import 本地化），逐文件 md5 与行为锁定见
[PROVENANCE.amc.md](PROVENANCE.amc.md) —— 算法与全部挑选参数数字未做任何修改。

## 在链路中的位置

```
esd2npz (26B Finalcorrection RUN<N>.npz + 本底 RUN<bkg>.npz)   ← 输入原生对接
   └─ calibsel AmC 支线（本文件所述流程）  → correlation_result_RUN<N>.npz
        ├─ prompt_energy ──→ O16 模板拟合 (fitter, O16Fitter)
        ├─ nH_energy    ──→ nH  纯高斯   (fitter, NhnCFitter)
        └─ delay_energy ──→ nC  纯高斯   (fitter, NhnCFitter)
                                   ↓ RUN<N>_{nH,nC,AmC}.npz
                          nlfit Stage5 → gamma_AllPhase.dat → dybmodel
```

## 用法

```bash
bash setup_env.sh                       # 首次：建 .venv
# 数据放 input/Data/：RUN<N>.npz（AmC run）+ RUN<bkg>.npz（本底，
#   run 号 = calib_to_analyze.txt 第三列；esd2npz 会自动补跑）
./run_pipeline.sh 10110                 # 单 run 关联挑选
# 或直调：
.venv/bin/python pipeline/run_amcsel_all.py --run 10110 \
    [--input-dir <dir>] [--out-dir <dir>] [--launched-by agent ...]
```

## 输出（每次运行自动留档）

```
output/<时间戳>/
  results/RUN<N>/correlation_result_RUN<N>.npz   ← 核心产物（三段能量+顶点）
  results/RUN<N>/Correlation_RUN<N>.pdf          ← 关联分析图（含俘获时间拟合）
  results/RUN<N>/xyz_distribution_RUN<N>.pdf     ← FV 优化图
  results/RUN<N>/fv_cuts_RUN<N>.npz              ← FV 切割条件
  timestamps/{prompt,delay,nH}/RUN<N>.txt        ← 时间戳
  run_log.{md,json} / config_snapshot.json / console.log / code/ + sha256
  （退出码：0=审计通过；3=审计失败（script 模式）；agent 模式降级为告警）
```

## 物理注意（使用前必读）

- **位置依赖**：ACU AmC 沿 z 轴扫描（Z −17.3 m … +17.3 m，中心 24 个 run）。
  与 AllPhase 历史表对比请用**中心 run**。样例：RUN10110（Z=0）三峰与历史差
  −0.30%/−1.13%/+0.35%；RUN10104（Z=+17.3 m）nH 偏 −6% —— 这是真实的
  位置依赖，不是 bug。
- 挑选参数（FV 能区、delay/nH/promt 窗口、distance_limit、dt_cut、中子源/
  普通源两套）全部取自原作者 `test.py` 原值（见 `config/paths.py` 注释），
  不要在本仓库改动这些数字；如需调整请回上游确认。
