# PROVENANCE — recon 模块（Stage −1: rtraw → ESD）

2026-08-27/28 建立。定位讨论与验证记录见仓库 memory 与本文末尾。

## 1. 本模块是什么、不是什么

- **是**：官方 junosw 重建链（`tut_rtraw2rec.py`）的编排包装 + OMILRECV2 overlay
  开关 + 输入清单生成 + 产物校验 + RunLogger 审计。`src/`、`pipeline/` 全部为本仓库
  自有编排代码（stdlib-only）。
- **不是**：任何重建算法的拷贝或修改。OMILRECV2 本体在 `../omilrec_opt/omilrecv2`
  （用户自己的优化项目，独立仓库独立版本）；官方基线 OMILREC 在 CVMFS J26.1.1 内。

## 2. 冻结的重建配置（逐一可溯源）

| 项 | 值 | 来源 |
|---|---|---|
| CVMFS 环境 | J26.1.1（`setup.sh` + `ExternalLibs/ROOT/6.30.08/lib` 加 PYTHONPATH/LD_LIBRARY_PATH） | omilrecv2 README + generate_reference.sh |
| 重建入口 | `${TUTORIALROOT}/share/tut_rtraw2rec.py --method steering-v2 --steering oec --use-mixedphase-in-steering` | 同上 |
| 波形刻度配置 | `RecConfigs/waverec_calib_reprod.yaml`，`--pmtcalibsvc-ChargeAlgType 0 --pmtcalibsvc-ReadDB 1` | 同上 |
| 事件重建配置 | `RecConfigs/evtrec_reprod_steering_using_OEC_woEcut.yaml`，`--output-stream /Event/Oec:on --fullLSmode --enableRDTimePdf` | 同上 |
| global tag | **ReProd26A_v1** | 同上（⚠️ 见 §5） |
| OMILREC 数值输入 | nPE map `LnPEMapFile_Ge68_Po214_reprod25D.root`、TimePdf `TimePdfFile_236rbin_Ge68_2025comb_reprod26A.root` + `TimePdfR3File_236rbin_fullLS.txt`、ChargeSpec `average_pdf-12144.root`，均在 `/data/juno/dingxf/OMILREC_maps/{nPEMap,TimePdf,ChargeSpec}/`，sha256 逐文件锁定于 `config/paths.py::MAP_ASSETS` | v1.0-postv107-gated `scripts/generate_reference.sh` 的 `verify_asset`（2026-08-27 本机逐一复核通过） |
| 其余 flag | `--cdcalibtq-npecut 0.2 --QPedThres 0.2 --OMILRECTQMode CalibNpeCut` | 同上 |

flag 集以 `config/paths.py::RECON_FLAGS` 为唯一权威；`src/rtraw_to_esd.py` 只拼装不增删。

## 3. 输入数据（rtraw）来源

- DAQ 全量档（首选）：`root://junoeos01.ihep.ac.cn//eos/juno/rtraw/<YYYY>/<MMDD>/RUN.<N>.JUNODAQ.<stream>.ds-*.global_trigger.*.rtraw`；run→日期查 `calibsel/calib_run_info/CalibRUN_from_file.csv`。
- 精选档（回退）：`/eos/juno/juno-rtraw/<VER>/global_trigger/<NN000>/<NNN00>/<N>/`（VER 依次试 J25.7.1/J25.7.0/J25.5.0）。
- 实测（2026-08-27，xrdfs）：10110 = 297 个文件（文件名 `Calib-ACU-AmC117-Global-Pos-x0y0z0`，中心位）；10104 = 198 个；12370 在精选档 J25.7.1（`Calib-ACU-Ge68-Global-Pos-x0y0z0`）。12628 样例（同事/`/data/juno/dingxf/inputs/index_12628_rtraw_1.json`，sha256 一致）= `Calib-CLSA-AmC100-Global-Pos-x0y-40z1740`。

## 4. OMILRECV2 overlay 机制

`InstallArea/python/sitecustomize.py` 预 import 影子模块，把链内 `CD-Vertex-omilrec`
（输出路径 `/Event/CdVertexRecOMILREC`）替换为 OMILRECV2 实现——steering 配置零改动。
本地构建：2026-08-27 在本机（AlmaLinux 9.4）对 `../omilrec_opt/omilrecv2`（detached
HEAD = v1.11.0）清空 `build/`+`InstallArea/` 后全新 cmake 构建；单测 11 项过 9 项，
其中正典 `test_fcn`（v107_rev1 金样本、1e-13 容差）通过；2 项失败
（fixture_tmle_ll/fixture_4stage_ll）为 v1.0.x 时代 `==` 精确等值的过期金样本，
源自 v1.6.0 起生产路径 float 双线性的**有意**算术变化（LL 差 ~2e-4，README 有记录），
非本机构建问题。

## 5. 已知口径差（未解决）

- 同事跑法 global tag = **ReProd26A_v1**；calibsel 默认消费的生产 ESD 为 **ReProd26B**。
  待办其一：向 Shubing Liu 确认 26B 对应 tag/steering；待办其二：同一切片
  "26A 本地重建 vs 26B 生产 ESD" 的 RecVertex 对比实验，量化差异。
- OMILRECV2 v1.11.0 与 CVMFS 基线差 ≤55 keV/150 mm（10 事例中 2 个高 z 敏感事例，
  OEC 初值改变 Minuit 收敛路径所致）；需逐位一致时用 `--impl baseline`
  或 omilrecv2 的 v1.0.7 tag。
- 数值口径对齐之前，本模块输出的物理数字不与生产 26B 数字混用/对比。

## 6. 端到端验证记录（2026-08-28，本机）

冒烟切片：`run_recon_all.py --runs 10110 --impl omilrecv2 --slice 1 --evtmax 100`

- `-1pre` 四件套 sha256 全过；`-1a` 297 文件中取 1（stream tag 解析正确）；
- `-1b` wrapper 全链跑通：日志含 `RecPoint:OMILRECV2.finalize … n_evt=57 … 249 ms/evt`
  （overlay 生效）与 `[verify] CdVertexRecOMILREC entries: 57`；
- `run_audit` PASSED（6 代码文件全 sha 一致；ESD + esd_list + config_snapshot 齐全）。
- **衔接**：该 ESD 经本地 MySimpleTag（`../JUNOSW_MyAlgz`，按 J26.3.1 编译）产出 EDM，
  CDCalib 57 条、`omilrec_{x,y,z,energy}` **57/57 有效**（无 -999）、Time 树 TLTime 正常；
  再经 calibsel `convert_edm_to_npz` 产出 `RUN10110.npz`（keys 与 AmC 支线输入完全一致，
  LivingTime=0.102 s）——即 rtraw→npz 的本地重建整扇门打开。

## 7. 关联模块改动

- `calibsel/pipeline/run_all.py`：新增 `--esd-list-dir`（recon 衔接；蕴含 `--full-esd`
  的 Stage 0；显式传入避免陈旧 `esd_list_<RUN>.txt` 复用）。
- `calibsel/config/paths.py`：MySimpleTag 的 JUNOSW_MyAlgz 优先用本地编译副本
  `../JUNOSW_MyAlgz`（2026-08-27 rsync 自 lustrefs、排除 341M Example、按 J26.3.1
  重编；lustrefs 原路径仍为回退）。
- 套件 `run_pipeline.sh`：新增 `[0/6] recon` 段（`RECON_IMPL` 环境变量开启，默认关），
  γ 分支在有 recon 清单时加 `--full-esd --esd-list-dir`。AmC 走本地重建还需
  calibsel run_all 出 `npz_corrected`（待 `--corrections-only` 模式，未做）。
