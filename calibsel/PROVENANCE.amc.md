# calibsel AmC 支线代码溯源（PROVENANCE）

**日期**：2026-08-27 · **范围**：本目录全部代码与配置（`input/Data/` 为运行数据，不含）

## 0. 总览表

| 本目录文件 | 源代码路径（ENL_agent = `/datafs/users/wujxy/agent-sci/ENL_agent/juno_calibration_acu_gamma_source`） | 类型 | 一句话改动 |
|---|---|---|---|
| `src/config_manager.py` | `correlate_selection/config_manager.py`（Shubing Liu, 2026-03-18） | **纯副本** | 零改动（md5 `73d06d7e3628` 一致） |
| `src/run_manager.py` | `correlate_selection/run_manager.py` | **纯副本** | 零改动（md5 `f289ec33b662`） |
| `src/base_analyzer.py` | `correlate_selection/base_analyzer.py` | **纯副本** | 零改动（md5 `a111c6340aa0`） |
| `src/bkg_loader.py` | `correlate_selection/bkg_loader.py` | **纯副本** | 零改动（md5 `84b65431b2c1`） |
| `src/correlation_analyzer.py` | `correlate_selection/correlation_analyzer.py` | 改编（1 行） | 仅第 20 行 import：`reconstruction_ana` → `local_reconstruction_ana`（见 §1） |
| `src/fv_selector.py` | `correlate_selection/fv_selector.py` | 改编（1 行） | 仅第 16 行 import：同上 |
| `src/local_reconstruction_ana.py` | `reconstruction_ana` 0.2.0 的 `LocalUtils.py`（`/workfs2/juno/shubingliu/my_python_pkg/reconstruction_ana_pkg/`） | 摘取内联 | 摘 4 个函数（`GetBinCenter`/`find_groups`/`getCoinTag`/`HistBasedLimitFinding`）逐行原样；另加 `PlotFitResult` 占位（本流程未调用，见 §2）。先例：`esd2npz/src/local_utils.py` 同源摘取 |
| `pipeline/run_amcsel_all.py` | 无直接源文件（流程逐步对标 `correlate_selection/test.py` 2026-04-14 版 main()） | **新写** | 编排 + RunLogger 留档；补调原作者的 `save_fv_cuts()` 归档切割条件（test.py 未调） |
| `pipeline/run_logger.py` | 本仓 `nlfit/src/run_logger.py` | 改编 | 模块名/配置快照字段本地化 |
| `config/paths.py`、`config/__init__.py`、`pipeline/__init__.py` | — | **新写** | 集中配置；分析参数逐字节取自 test.py 原值 |
| `calib_run_info/calib_to_analyze.txt` | 同名文件 | **纯副本** | 零改动（md5 `19a16bd4b8a2`） |
| `calib_run_info/CalibRUN_from_file.csv` | 同名文件 | **纯副本** | 零改动（md5 `70aaa23cf08f`） |
| `run_pipeline.sh`、`setup_env.sh`、`requirements.txt`、`README.md` | — | **新写** | 环境/文档 |

未并入（本流程不需要）：`correlate_selection/dn_analyzer.py`、`fix_timestamps.py`
（无 import 关系）、`correlation_analyzer.raw.py`（历史版本留档）。

## 1. 唯一的代码改动：两行 import

原作者包依赖 IHEP 集群上的 `reconstruction_ana`（editable 安装）。并入方式与
esd2npz 相同：把实际用到的 4 个函数摘到本模块 `local_reconstruction_ana.py`
（函数体逐行原样），再把两个文件的 import 行指过去：

```diff
- from reconstruction_ana import GetBinCenter, getCoinTag, PlotFitResult   # correlation_analyzer.py L20
+ from local_reconstruction_ana import GetBinCenter, getCoinTag, PlotFitResult
- from reconstruction_ana import HistBasedLimitFinding, GetBinCenter       # fv_selector.py L16
+ from local_reconstruction_ana import HistBasedLimitFinding, GetBinCenter
```

除这两行外，六个 `.py` 与源逐字节一致（`diff` 输出仅上述两行，md5 见总览表）。

## 2. 行为锁定验证（2026-08-27）

输入 `RUN10104.npz`（AmC117 @ Z=+17.3m，与生产侧
`/lustrefs/.../Finalcorrection_from_npzESD/Data/RUN10104.npz` 数组逐位一致）
+ 本底 `RUN10100.npz`（与生产侧文件字节一致）：

- 本模块输出 `correlation_result_RUN10104.npz` 与生产侧
  `correlate_selection/Results_fromFinalcorrection/RUN10104/` 同名文件
  **逐数值一致**（34308 关联对、30205 nH 候选、nH 谱峰 bin 2.09 / counts 730、
  俘获时间 τ=210.6±2.1 μs）。
- 中心 run `RUN10110`（AmC117 @ Z=0，BKG 10100）：39147 对、38689 nH 候选、
  τ=211.2±2.0 μs；三峰拟合 nH 2.2193 / nC 5.0239 / O16 6.3023 MeV，与
  AllPhase 历史表（2.2259/5.0814/6.2806）偏差 −0.30%/−1.13%/+0.35%。

## 3. 数据来源（input/Data/）

| 文件 | 来源 | 说明 |
|---|---|---|
| `RUN10110.npz` | `scp lidian@lxlogin002:/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/Finalcorrection_from_npzESD/Data/RUN10110.npz` | 生产 26B Finalcorrection 输出，AmC117 @ 中心 |
| `RUN10100.npz` | 同上目录（字节与 lin 本地遗留副本一致） | 本底（PhysicsRun） |
| `RUN10104.npz` | 同上目录 | 边缘 Z=+17.3m 样例（演示位置依赖：nH≈2.09，−6%） |
| `RUN10104.local_regen_20260820.npz` | lin 本地 2026-08-20 重生成版 | 数组与生产版逐位一致（仅压缩不同）；留作对照 |

上游链路：ESD→EDM→npz→26B Finalcorrection 由本仓 `esd2npz/` 承担
（其输出即本模块输入，目录/键名原生对接：`RUN<N>.npz`，
键 `omilrec_{x,y,z,energy}` / `global_time_s` / `LivingTime`）。

## 4. 复核清单

```bash
SRC=/datafs/users/wujxy/agent-sci/ENL_agent/juno_calibration_acu_gamma_source
md5sum $SRC/correlate_selection/config_manager.py  calibsel/src/amc/config_manager.py
diff  $SRC/correlate_selection/correlation_analyzer.py calibsel/src/amc/correlation_analyzer.py  # 仅 L20
diff  $SRC/correlate_selection/fv_selector.py          calibsel/src/amc/fv_selector.py          # 仅 L16
diff  <(git show cda3b93b:...) # n/a
# GaussianFitter 逐字节：对比 fitter/src/NhnCFitter.py 与
# $SRC/AmC_nH-nC_fitter/npz_fromFinalcorrection/nH_nC_fitter.py 的 class 体
```
