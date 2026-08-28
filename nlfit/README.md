# nlfit — 非线性全局拟合模块（Stage 4b/5/6/7）

把 peakfit 的峰位结果变成 **E_true = f(E_rec)**：

```text
peakfit/results/RUN{N}_{src}.npz ──┐
                                  ├─ Stage 5  聚合 → gamma_AllPhase.dat（7 峰，
external_inputs/（MANIFEST 契约）─┘            dyb 顺序 Cs137 Mn54 Ge68 nH Co60 nC O16）
                                  → Stage 6  dybmodel C++ 全局 NL 拟合（原版，SL6 容器）
                                  → Stage 7  反演 → Etrue_from_Erec_lookup.npz/csv
```

## Stage 一览

| Stage | 内容 | 输出 |
| --- | --- | --- |
| 4b | 外部数据契约校验（sha256 vs MANIFEST） | run_log 记录 |
| 5 | 聚合：γ 源 μ（provider=fitter）+ AmC 三峰 μ（provider=amc，RUN10110）→ 7 峰表；缺失自动钉历史值+告警 | `results/gamma_AllPhase.dat`（+ provenance、meanEscaleEres 表）、`figures/stage5_gamma_peaks.*` |
| 6 | dybmodel 全局拟合（原版 C++，自建 SL6 容器内运行） | `results/bestFit_*.dat`、`nl_curves.tsv`、`figures/stage6_nl_curves.*`、`figures/dybmodel/*.pdf` |
| 7 | E_rec→E_true 反演（纯 Python，单调性+往返误差校验） | `results/Etrue_from_Erec_lookup.npz/.csv`、`figures/stage7_inversion.*` |

## 运行

```bash
bash setup_env.sh                      # 一次
bash run_pipeline.sh --fitter-results <peakfit输出>/results --out-dir <目录>
bash run_pipeline.sh ... --skip-dybmodel    # 只跑 4b+5（无 ROOT 环境时）
bash run_pipeline.sh ... --validate-ref     # Stage 6 与历史 bestFit 数值对比（行为锁）

# 分 phase 非线性拟合（run 自动选：该 phase 区间内的中心 run，|z|≤0.5 m）
bash run_pipeline.sh ... --phase 1 --out-dir <目录>/phase1
bash run_pipeline.sh ... --phase 3 --nc-pin      # nC 钉生产值 5.08140（对齐口径）
bash run_pipeline.sh ... --phase 2 --runs-override 'Cs137=12118,Ge68=12370'  # 手工指定
```

顶层 `run_pipeline.sh`（仓根）已把本模块作为第三段自动接入。

## 分 phase 模式（--phase N）

- **phase 清单数据驱动**：读 `calibsel/input/correction/data/ValProd26BPhase.csv`
  （与 26B 修正共用同一份 run 区间表，唯一事实源）。
- **run 挑选**：phase 区间内该源的全部**中心 run**（|z|≤0.5 m，与生产
  `meanEscaleEres_perPhase_CDcenter` 同口径），μ 取各 run 结果的
  **方差倒数加权平均**；`--phase 1` 默认把区间前的 2025-08 试运行周并入
  P1（生产 `gamma_Phase1_K40.dat` 即如此；`--no-fold-pre` 关闭）。
- **缺峰剔除而非钉值**：某源在该 phase 没有可用结果就从表中剔除并告警
  （AllPhase 模式仍保持"钉历史值"旧行为，字节级不变）。可用性：
  P2/P3 六峰、P4 六峰（三源各仅 1 个中心 run）、P1 五峰
  （γ 单能源只有 8 月周并入后可用）、K40 仅 P1（且不入 7 峰表）。
- **isotope 谱自动切换**：sandbox 内把该 phase 的
  `Isotope_data_Phase{N}_FVcutR0_1720_Finalcorrection.root` 物化到 C++
  固定打开的 AllPhase 文件名（`dybParameters.cxx:199-201`）——
  不改同事代码、不重编译；映射表在 `config/paths.py::ISOTOPE_ROOT_BY_PHASE`。
- **nC 口径**：生产所有分相表把 nC 钉在 5.08140；本模块默认用实测值，
  `--nc-pin` 切到生产口径（当前实测 5.024，差 −1.1%）。

### 新增一个 phase 的操作清单（改数据不改代码，仅 1 行映射）

1. `calibsel/input/correction/data/ValProd26BPhase.csv` 加一行 run 区间；
   同时需要 26B 生产侧交付的 `phase{N}_model.npz` + 绝对能标
   （放 `calibsel/input/correction/`；没有则区间外 run 按就近 phase 修正，
   见 `correction_api.phase_from_run`）。
2. `calibsel/calib_run_info/{CalibRUN_from_file.csv, calib_to_analyze.txt}`
   补该 phase 的 run（生产侧本来就会更新）。
3. dybmodel `necessaryfiles/.../Spec/forNLfitter/` 放入该 phase 的
   `Isotope_data_Phase{N}_*.root`，并在 `config/paths.py::
   ISOTOPE_ROOT_BY_PHASE` **加一行映射**（唯一要动的代码处）。
4. `--phase N` 直接跑；run 挑选、缺峰剔除、产物命名
   （`gamma_Phase{N}.dat`）、审计全部自动。

## 关键设计

- **原样运行（remote-container，首选）**：dybmodel 的**原版代码与预编译二进制**
  在其原生 SL6 / J17v1r1（ROOT5）环境里跑——通过 `hep_container exec SL6 -g juno`
  在 lxlogin002 上执行（本节点没有 container.ihep.ac.cn）。**C++ 零修改**：
  每 run 的 gamma 表复制到原路径 `necessaryfiles/.../gamma_AllPhase.dat`
  （跑完恢复原值；工作区每次 rsync 自 ENL_agent 源树，状态自愈）。
  串行运行（每工作区同时一个拟合）。
- **本地回退（local）**：远程节点不可用时，用 el9 ROOT 6.30.08 重编
  `nlfit/_dybmodel/`（自动重建，不入库），带两处**非物理**补丁：
  ① `SetBatch`（headless）② `DYB_GAMMA_DAT` 环境变量注入 gamma 表。
  行为锁定：中心值与历史基线一致到 ~0.1%。
- **C++ main() 成功也返回 1**：成功与否只看 bestFit/curves 输出是否产生。
- **误差约定**：dat 的 `err_mu` 列是**总相对误差**（历史约定全 7 峰 0.005）。
  peakfit 给的是纯统计误差（如 Ge68 2e-4），聚合时按下限 `MU_ERR_FLOOR=0.005`
  兜底（`config/paths.py` 可调/关闭），避免过度加权。
- **AmC 三峰**：nH/nC/O16 已由 `calibsel` AmC 支线 + `peakfit run_amc_fit_all` 提供
  （provider=amc，RUN10110 = AmC117@中心；结果缺失时仍自动钉历史值+告警）。
  O16 拟合的 minuit HESSE 可能失败（参数贴界）→ μ 误差不可用，由
  `MU_ERR_FLOOR` 兜底，fit_valid 如实记入 run_log。
- **外部数据契约**：过渡期历史值仍留 `external_inputs/MANIFEST.json`；
  连续谱由 dybmodel 自带
  `Isotope_data_*.root` 提供（同属外部依赖，sha256 记录）。
- **E_true 约定**：Ge68=1.022 MeV（湮灭对）、Co60=2.506 MeV（级联和）——
  dyb 约定，与 peakfit 内部 E_scale 锚点（Ge68 0.8845）含义不同，见
  `config/paths.py` 注释。
- **留档与审计**：run_log.{md,json} / config_snapshot / console.log / code+sha256
  快照 / 结束完整性审计（脚本模式 exit 3，agent 模式警告）——与
  calibsel、peakfit 同一契约。

## 依赖

- Python：numpy / scipy / matplotlib（`.venv`，`setup_env.sh` 自建）
- Stage 6：自建 SL6 容器资产（见 `container/README.md`，`tools/setup_container.sh`
  一键布防到 `/datafs/users/wujxy/containers/dybmodel-sl6/`）+ 本机 apptainer
  （`--userns` 模式，无需 root/setuid）+ `DYBMODEL_SRC`（ENL_agent 姊妹工作区，只读）
- 曲线导出（dump_curves.C）：`config/paths.py::CVMFS_SETUP`（el9 ROOT 6.30.08）
