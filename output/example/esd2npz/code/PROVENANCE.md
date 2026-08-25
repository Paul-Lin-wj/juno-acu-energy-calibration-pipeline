# standalone_esd2npz 代码溯源与环境变动说明

**日期**：2026-08-24 · **范围**：本目录下全部代码文件（`data/` 为运行产物，不含）
**验证方式**：每项声明均于 2026-08-24 用 `md5sum` / `cmp` / `diff` / `ast` 比对或路径存在性检查实测确认，复核命令见文末 [§5 复核清单](#5-复核清单)。

---

## 0. 2026-08-24 规范化重构补记（不影响任何算法）

目录与流程按 `standalone_fitter` 风格规范化，**`src/` 与 `input/correction/`
一字节未动**（md5 与下表一致）：

- 新增 `pipeline/`（`run_all.py` 总调度 / `run_logger.py` 审计留档 /
  `cuts_parser.py` 挑选条件归档）、`tools/`（物理 QA 与逐位审计）、`skills/`（10 篇使用文档）；
- 原 `run_pipeline.sh` 改为薄封装，默认模式 **from-edm**（即原 `--skip-esd`，
  从 `REMOTE_EDM_DIR` 预置 EDM 开始），`--full-esd` 才做本机重建；
- 输出统一进 `output/<时间戳>/{results,figures,cuts,logs,code_snapshot}/`，
  `data/` 仅保留为手动运行 `src/*.py` 时的传统输出位；
- 每次运行自动归档：run_log.{md,json}、config_snapshot.json、console.log、
  code_snapshot（含 sha256）、**cuts/{R}_cuts.json（全部挑选条件，运行时值
  +静态定义）**。

---

## 1. 总览表

| 本目录文件 | 源代码绝对路径 | 类型 | 一句话改动 |
|---|---|---|---|
| `src/convert_edm_to_npz.py` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/npz_from_root/convert_root_to_npz.py` | 改编 | CLI 与路径本地化；转换主循环不变 |
| `src/apply_final_correction.py` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/apply_final_correction.py` | 改编 | CLI 与导入路径本地化；修正算法逐行不变 |
| `src/combine_selection.py` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/singles_selection/CombineSelection.py`（仓库版） | 改编 | 仅文件头 ~119 行：导入/路径/CLI；算法主体逐行不变 |
| `src/local_utils.py` | `/workfs2/juno/shubingliu/my_python_pkg/reconstruction_ana_pkg/reconstruction_ana/LocalUtils.py`（`reconstruction_ana 0.2.0`，editable 安装） | 改编（内联） | 摘取 4 个函数；1 处语义微调（memory 打印） |
| `src/list_esd.py` | 无直接源文件（逻辑派生自 `EDM_from_esd/sh_job/run_batch.sh` 第 56/62/91-94 行 + `calib_run_info/datasource_paths.py` 的路径常量） | **新写** | 用 CVMFS `xrdfs` 替代集群 `eos ls` |
| `src/esd_to_edm.py` | 无直接源文件（重建命令派生自 `EDM_from_esd/sh_job/run_batch.sh` 第 19-20、133-137 行） | **新写** | 生成 wrapper：source CVMFS+JUNOSW 后跑 `run.py`，支持切片 |
| `run_pipeline.sh` | 无直接源文件（整合 `calib_selection/run.sh`、`Finalcorrection_from_npzESD/sh_job/run.sh`、顶层 `run.sh` 的行为） | **新写** | 一键五段式 + 自动补跑本底 run |
| `config/paths.py`、`config/__init__.py` | — | **新写** | 集中配置（本目录唯一需按环境修改的文件） |
| `setup_env.sh`、`requirements.txt`、`README.md`、`.gitignore` | — | **新写** | 环境/依赖/文档 |
| `input/correction/correction_api.py` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/input/correction_api.py` | **纯副本** | 零改动 |
| `input/correction/data/{phase1..4}_model.npz`、`time_correction_v2.csv`、`ValProd26BPhase.csv`、`vertex_correction_26B.csv`（7 个文件） | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/input/data/` 同名文件 | **纯副本** | 零改动 |
| `calib_run_info/calib_to_analyze.txt` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/calib_run_info/calib_to_analyze.txt` | **纯副本** | 零改动 |
| `calib_run_info/CalibRUN_from_file.csv` | `/datafs/users/lin/workplace/energy_reco/ENL_agent/juno_calibration_acu_gamma_source/calib_run_info/CalibRUN_from_file.csv` | **纯副本** | 零改动 |
| `lib/libpcre.so.1` | `/cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202105/lib/libpcre.so.1`（symlink → `libpcre.so.1.2.12`，`cp -L` 实体化） | **二进制副本** | 零改动（292,696 B） |

**外部引用（未复制，运行 Stage 0 时访问）**：

| 绝对路径 | 用途 |
|---|---|
| `/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/setup.sh` | JUNO 离线软件环境（Sniper/ROOT/xrootd 5.7.3 客户端） |
| `/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/ExternalLibs/xrootd/5.7.3/bin/xrdfs` | ESD 目录列举 |
| `/lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/InstallArea/setup.sh` | MySimpleTag 算法环境（InstallArea 构建日期 2026-06-06） |
| `/lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/SimpleTagAlgz/share/run.py` | ESD→EDM 重建入口（Sniper 任务 MySimpleTag） |
| `/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data` | 预置 EDM 数据（`--skip-esd` 时的 Stage 1 输入，2799 分块） |

---

## 2. 逐文件改动明细

### 2.1 `src/convert_edm_to_npz.py`（改编）

源：`…/juno_calibration_acu_gamma_source/npz_from_root/convert_root_to_npz.py`（Shubing Liu，2026-03-26，原文件 167 行）。

**未改动**（语句级 diff 确认，仅措辞/写法差异）：
- 分支列表 `global_time_s, global_time_ns, trigger_type, MuonVeto, totalPE, omilrec_x/y/z, omilrec_energy`；
- `get_chunk_sort_key()`（按 `run_<id>_<start>_<end>.root` 数值排序）；
- 主循环：`uproot.open` → `CDCalib.arrays(..., library="np")` 逐分支追加 → `Time` 树 `TLTime_s/TLTime_ns`（或旧式 `TLTime`）累加 LivingTime → `np.concatenate` → `np.savez(RUN{run}.npz)`；
- 唯一文字差异：TLTime 缺失警告语（`"Could not find TLTime information"` → `"no TLTime information"`），空分支的 `if/else` 改三元表达式（语义相同）。

**改动**：
1. 路径来源：原 `from datasource_paths import edm_data_dir, npz_root_input_dir, ...`（依赖 `calib_run_info/datasource_paths.py` 及 `--datasource esd|miniesd`）→ 改为本项目 `config/paths.py` 的 `EDM_DIR`/`NPZ_RAW_DIR`；
2. CLI：`--run` 由可选变**必填**（删除 9000–16000 全量批处理模式，该模式依赖原项目的多数据源目录布局）；新增 `--input-dir`（可指向 lustrefs 预置 EDM）、`--out-dir`；
3. 删除 `--datasource` 参数与 miniesd 分支（本包只做 ESD 链路）。

### 2.2 `src/apply_final_correction.py`（改编）

源：`…/juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/apply_final_correction.py`。
注：lustrefs 部署版（`/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/Finalcorrection_from_npzESD/apply_final_correction.py`）与仓库版 `cmp` 一致，二者等价。

**未改动**（grep 逐行确认 `corr.*` 调用序列字节级一致）：
`correct_vertex_rbias(position_unit="mm")` → `spatial_factor_from_position(...)` → `time_factor(event_time)` → `phase_from_run(run)` → `absolute_scale_for_phase(phase)` → `total_factor = spatial * abs_scale / time_factor` → `energy_corr = float64(energy) * total_factor` → 各量 `astype` 回原 dtype 写回；输入 npz 的键与输出键不变。

**改动**：
1. `from correction_api import EnergyCorrection26B` 的搜索路径：原指向 `…/Finalcorrection_from_npzESD/input/` → 本目录 `input/correction/`（数据已复制）；
2. CLI：原为单位置参数 `<RUN_NUM>`，输入/输出目录是脚本内硬编码常量（`INPUT_DIR`/`OUTPUT_DIR`）→ 改为 `run --input --out-dir`（默认值仍等价于本项目目录布局）；`run_num` 原来取自 `sys.argv[1]`，现在取自 CLI `run` 位置参数。

### 2.3 `src/combine_selection.py`（改编）

源：`…/juno_calibration_acu_gamma_source/singles_selection/CombineSelection.py`（仓库版，968 行；本文件 976 行）。
注：lustrefs 部署版与仓库版仅 4 行差异（`resolve_selection_paths` 里 Finalcorrection 输入路径的写法不同，均指向同一数据目录）；**本包以仓库版为源**。

**未改动**（diff 确认：全部改动位于原文件第 1–111 行；自原文件第 112 行（`CALIB_INFO_FILE`）起至 EOF 两文件**逐行一致**，含 `get_run_config`、`apply_muon_veto`、`fit_quadratic_plus_gaussian_grid`、`find_peak_region`、`load_npz`、`resolve_reco_keys`、ROI/ρ/Z-cut/EFV/能量窗主流程、npz/时间戳/图输出逻辑）：
- ROI 稳健扫描（`find_peak_region` 的 mu±nσ 网格拟合）；
- Z-cut 稳健判据（`find_omilrec_vertex_zcut`，RD 阈值 5 点检查）；
- 能量窗（mu±3σ）与 EFV 事件计数、`calib_index` 输出键名（`calib_omilrec_energy/x/y/z`）。

**改动**（均在文件头部）：
1. 删除未使用的 `import uproot as up`、`import awkward as ak`、`from tqdm import tqdm`（原文件中这三者从未被调用）；
2. `from reconstruction_ana import *`（原包 editable 安装于 `/workfs2/…`，含 numba/mypyc 编译链）→ `from local_utils import GetBinCenter, HistBasedLimitFinding, save_arrays_to_text, get_memory_usage`；
3. `resolve_selection_paths()`：原按 `datasource/ecorrection/finalcorrection` 在**原项目目录树**内选路径（Finalcorrection 模式读 `/lustrefs/…/Finalcorrection_from_npzESD/Data`，写到 `singles_selection/Results_fromFinalcorrection`）→ 固定为本项目 `data/npz_corrected` → `data/selection`；
4. CLI：`--datasource/--Ecorrection/--Finalcorrection` 保留为兼容占位（不再参与路径选择），新增 `--input-dir/--out-dir`；删除原 `--Finalcorrection` 与 `--Ecorrection` 互斥报错（路径已不再依赖它们）。

### 2.4 `src/local_utils.py`（内联，4 函数）

源：`/workfs2/juno/shubingliu/my_python_pkg/reconstruction_ana_pkg/reconstruction_ana/LocalUtils.py`（`reconstruction_ana 0.2.0`，dist-info 确认；editable 安装，原 ROOPY venv 即从此路径加载）。AST 逐函数比对结果：

| 函数 | 比对结果 | 说明 |
|---|---|---|
| `GetBinCenter` | 1 行差异 | `bins` 前加 `np.asarray()` 防御转换；对 numpy 输入语义完全相同 |
| `HistBasedLimitFinding` | 语句级一致 | 仅 2 处长条件表达式换行（纯格式） |
| `save_arrays_to_text` | 语句级一致 | 仅 docstring 合并为一行 |
| `get_memory_usage` | **有意改动** | 原版 `import psutil` 硬依赖 → 改为 psutil 可选 + `/proc/{pid}/statm` 兜底；**只影响打印的内存 MB 值，不影响任何数据/结果** |

### 2.5 `src/list_esd.py`（新写）

无单一对应源文件；逻辑派生自：
- `…/EDM_from_esd/sh_job/run_batch.sh`：block 目录推导（`run//1000*1000`）、子目录前缀匹配（`{sub}_CalibData_phase{N}`）、ESD 计数（第 56、62 行）、`XROOTD_PREFIX="root://junoeos01.ihep.ac.cn/"` 拼接文件清单（第 91-94 行）；
- `…/calib_run_info/datasource_paths.py`：`XROOTD_PREFIX`、`EOS_GLOBAL_TRIGGER` 等路径常量定义。

与原逻辑的**功能等价替换**：`eos ls <EOS 路径>`（集群 eos 客户端）→ `xrdfs root://junoeos01.ihep.ac.cn ls <路径>`（CVMFS xrootd 5.7.3）。
**新增**：URL 采用 CERN EOS 双斜杠形式 `root://host//eos/…`（见 §3.1 坑 1）。

### 2.6 `src/esd_to_edm.py`（新写）

重建命令派生自 `…/EDM_from_esd/sh_job/run_batch.sh` 第 19-20、133-137 行：

```bash
# 原（集群 LSF 作业内）：
source /cvmfs/.../J26.3.1/setup.sh
source /lustrefs/.../JUNOSW_MyAlgz/InstallArea/setup.sh
python .../SimpleTagAlgz/share/run.py --evtmax -1 --loglevel Fatal \
    --input-list <list> --user-output <out>
```

新文件把上述命令生成进一个 bash wrapper（`tempfile` 创建、跑完删除），并新增：
- **切片**：`--start/--end`（0-based 含端点）用 `sed -n` 截取 ESD 清单子集（冒烟测试用，原脚本无此能力）；
- **libpcre 兜底**（§3.1 坑 2）；
- `RUNNUM` 环境变量传给 wrapper 用于切片文件名。

### 2.7 `run_pipeline.sh`（新写）

整合三个原入口脚本的行为：
- `…/juno_calibration_acu_gamma_source/run.sh`（`source ROOPY && python …/CombineSelection.py $RUN`）；
- `…/Finalcorrection_from_npzESD/sh_job/run.sh`（`source ROOPY && python apply_final_correction.py <RUN>`）；
- `…/calib_selection/run.sh`（`--Finalcorrection` 分发到 CombineSelection）。

**新增逻辑**：
- `--skip-esd` / `--slice N` / `--edm-input DIR` 三种 EDM 输入模式（原流水线各 stage 独立跑、人工衔接）；
- **Stage 2b 本底自动补跑**：从 `calib_run_info/calib_to_analyze.txt` 解析 `Source,CalibRun,BkgRun` 映射，若本底 run 的修正后 npz 缺失则自动对其跑 Stage 1-2（原流程要求本底数据已存在）。

### 2.8 `config/paths.py`（新写）

集中全部可配置项：本地数据目录、CVMFS/JUNOSW 路径、xrootd host、ESD 基址、预置 EDM 目录、`LIB_FALLBACK_DIRS`、`TEST_RUN=12370`。是本目录**唯一需要按部署环境修改**的文件。

### 2.9 纯副本文件（零改动，md5/cmp 验证）

| 文件 | md5（源=副本） |
|---|---|
| `input/correction/correction_api.py` | `8ce74ba51618feee85f12a24e33d7f17` |
| `calib_run_info/calib_to_analyze.txt` | `19a16bd4b8a2a55b1705e3ac5ea8318d` |
| `calib_run_info/CalibRUN_from_file.csv` | `70aaa23cf08f41599c760878ea2f353e` |
| `input/correction/data/` 7 个文件 | `cmp -s` 全部 IDENTICAL |

### 2.10 `lib/libpcre.so.1`（二进制副本）

`cp -L` 自 CVMFS anaconda3-202105（symlink 实体化为 `libpcre.so.1.2.12`，PCRE 1.2.12）。
md5 两侧一致：`68c5ae0c78add3df00ea9ed389ba973a`。仅依赖 `libc`，与系统 glibc 2.39 兼容（实测加载成功）。

---

## 3. 环境变动说明

### 3.1 与原运行环境的逐项对比

| Stage | 原运行环境 | 新运行环境 | 变动与影响 |
|---|---|---|---|
| **0：ESD→EDM** | LSF 计算节点（`hep_sub` 提交）；集群自带 `eos` CLI 列目录；CVMFS `J26.3.1` + `JUNOSW_MyAlgz`（2026-06-06 构建）；EL9 系统库 | **本机直接运行**（无作业队列）；`xrdfs`（CVMFS 内 xrootd 5.7.3）列目录；**同一版本** CVMFS `J26.3.1` + **同一构建** `JUNOSW_MyAlgz`（2026-06-06）；glibc 2.39 系统 | ① CVMFS/JUNOSW 软件版本**零变动**（重建算法与原版完全相同的二进制）；② 文件列举工具 eos CLI → xrdfs（仅列举，不参与重建）；③ ESD 读取 URL 改双斜杠（见下）；④ 补 `libpcre.so.1`（见下） |
| **1：EDM→NPZ** | 原脚本未声明环境；ROOPY venv 装有 uproot 5.7.3（项目无 lock 文件，实际运行环境未在项目内声明） | 本目录 `.venv`：Python 3.12.3 + **uproot 5.7.6** | uproot 5.7.3→5.7.6。**影响已验证**：对 RUN 12370 的 8 个分块输出与远程参考 npz 逐位一致（maxdiff=0） |
| **2：Finalcorrection** | ROOPY venv（Python 3.12.12；numpy 2.4.4、pandas 3.0.2、scipy 1.17.1），`sh_job/run.sh` 设 `OPENBLAS_NUM_THREADS=1`、`OMP_NUM_THREADS=1` | `.venv`：Python 3.12.3；numpy 2.5.2、pandas 3.0.5、scipy 1.18.1；**未设**线程数限制 | 包版本较新；线程数限制只影响 CPU 占用不影响数值。**影响已验证**：phase3 `absolute_scale=0.99743135` 与交接文档/参考输出一致，修正后 npz 与参考逐位一致 |
| **3：Selection** | ROOPY venv（Python 3.12.12；**reconstruction_ana 0.2.0 editable**（mypyc 编译 + numba 0.65.0）、awkward 2.9.0、tqdm 4.67.3、uproot 5.7.3、psutil 7.2.2、numpy 2.4.4、matplotlib 3.10.8、pandas 3.0.2、scipy 1.17.1） | `.venv`：Python 3.12.3；numpy 2.5.2、pandas 3.0.5、scipy 1.18.1、matplotlib 3.11.1、uproot 5.7.6；**无** reconstruction_ana/awkward/numba/tqdm/psutil（4 个用到的函数已内联，其余为未使用导入） | 唯一语义差异：`get_memory_usage` 无 psutil 时走 `/proc` 兜底（只影响日志打印）。**影响已验证**：selection 输出（109212 事件 × 5 字段）与参考输出**全部 maxdiff=0** |

结论：**除 Stage 0 的运行位置（集群→本机）与列举工具（eos→xrdfs）外，所有 Python 依赖均为 pip 可装的开源包且版本更新**；JUNO 侧软件（CVMFS/JUNOSW）版本未变。所有数值影响均已用"与参考输出逐位对比"实测排除（见 `README.md` 验证记录）。

### 3.2 过程中发现并固化的环境坑

1. **EOS xrootd 双斜杠 URL**：本机 CVMFS xrootd 5.7.3 客户端要求 `root://junoeos01.ihep.ac.cn//eos/…`（host 后两个 `/`，CERN EOS 命名空间约定）；单斜杠被服务端拒绝（`[3010] Opening relative path … is disallowed`）。原集群脚本用单斜杠可通（客户端/服务端组合不同）。**已固化**：`list_esd.py` 生成双斜杠 URL。
2. **libpcre.so.1 缺失**：EL9 集群自带 PCRE1；本机（PCRE2-only）上 Sniper 加载失败。且**不能**把 anaconda 整个 lib 目录加进 `LD_LIBRARY_PATH`（其旧 `libstdc++.so.6` 会遮蔽系统库，报 `GLIBCXX_3.4.29 not found`）。**已固化**：`setup_env.sh` 单文件拷贝到 `lib/`，wrapper 只加 `lib/` 目录。
3. **xrdfs 需 CVMFS 完整环境**：裸 PATH 前缀不够（缺 `LD_LIBRARY_PATH`）。**已固化**：`list_esd.py` 用子 shell `source setup.sh && env` 捕获完整环境（带缓存）。

### 3.3 取舍说明（为什么这么改）

| 取舍 | 理由 |
|---|---|
| Stage 0 保留 CVMFS+JUNOSW 外部依赖 | 重建是 C++ Sniper 任务，无法用 pip 复现；且 CVMFS 是只读共享挂载，版本锁定反而利于可复现 |
| 内联 4 个函数而非 `pip install reconstruction_ana` | 原包是 editable + mypyc 编译 + numba 依赖链，且实际只用到 4 个纯函数；内联后去掉对 `/workfs2` 个人目录的硬依赖（该路径不属于本项目，随时可能失效） |
| `--run` 必填、删除全量批处理模式 | 全量模式耦合原项目的多数据源目录布局（esd/miniesd 双树）；本包按 run 驱动，批处理交给外层脚本 |
| 数据不随包（`data/` 进 .gitignore） | ESD/EDM/NPZ 为数百 GB 量级；包内只内置 212KB 修正模型（属算法的一部分） |
| `--slice` 切片能力 | 原脚本无；用于低成本冒烟测试 ESD→EDM 链路（1 文件 ~5 min） |
| 本底 run 自动补跑 | 原流程要求人工保证本底数据存在；`calib_to_analyze.txt` 已含映射，自动化无额外信息需求 |

---

## 4. 已知差异与限制（如实记录）

1. **Stage 0 重建的 `totalPE` 分支**与 2026-05-20 生成的参考 EDM 存在微小差异（97% 事件差 <0.3%，个别事件至 ~8%）——参考 EDM 由 5 月版 JUNOSW 生成，本环境用 6 月版（2026-06-06 构建）；`omilrec_energy/x/y/z`、`global_time_s/ns`、`MuonVeto` **逐位一致**，下游不使用 `totalPE` 的修正链路不受影响。
2. **双斜杠 URL 未在集群上回测**：本包生成的 URL 只在本机验证；若未来要回到集群跑 Stage 0，建议先用 1 个文件冒烟。
3. **Stage 1-3 的 Python 包版本未锁定**（`requirements.txt` 只给下限）；当前 venv 实际版本见 §3.1，逐位一致性已用当前版本验证。
4. 完整 run 的 ESD→EDM（147 个 ESD，~75GB）未实测（小时级）；切片（1 与 3 文件）已实测。

## 5. 复核清单

以下命令可逐条复核本文档声明（在本目录或源目录下执行）：

```bash
cd /datafs/users/lin/workplace/energy_reco/ENL_agent

# (1) 纯副本 md5
md5sum juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/input/correction_api.py \
       standalone_esd2npz/input/correction/correction_api.py
md5sum juno_calibration_acu_gamma_source/calib_run_info/calib_to_analyze.txt \
       standalone_esd2npz/calib_run_info/calib_to_analyze.txt
md5sum juno_calibration_acu_gamma_source/calib_run_info/CalibRUN_from_file.csv \
       standalone_esd2npz/calib_run_info/CalibRUN_from_file.csv
# (2) 7 个修正数据文件逐字节
for f in phase1_model.npz phase2_model.npz phase3_model.npz phase4_model.npz \
         time_correction_v2.csv ValProd26BPhase.csv vertex_correction_26B.csv; do
  cmp juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/input/data/$f \
      standalone_esd2npz/input/correction/data/$f && echo "$f OK"
done
# (3) 改编文件 diff（应只看到 §2 所列头部/CLI 差异）
diff juno_calibration_acu_gamma_source/npz_from_root/convert_root_to_npz.py \
     standalone_esd2npz/src/convert_edm_to_npz.py
diff juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/apply_final_correction.py \
     standalone_esd2npz/src/apply_final_correction.py
diff juno_calibration_acu_gamma_source/singles_selection/CombineSelection.py \
     standalone_esd2npz/src/combine_selection.py
# (4) local_utils 四函数 AST 比对（§2.4 的脚本）
# (5) libpcre md5
md5sum standalone_esd2npz/lib/libpcre.so.1 \
       /cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202105/lib/libpcre.so.1.2.12
# (6) 外部引用路径存在性
ls /cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/setup.sh \
   /cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/ExternalLibs/xrootd/5.7.3/bin/xrdfs \
   /lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/InstallArea/setup.sh \
   /lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz/SimpleTagAlgz/share/run.py
# (7) venv 版本
standalone_esd2npz/.venv/bin/python -c "import sys,numpy,pandas,scipy,matplotlib,uproot;print(sys.version.split()[0]);[print(m.__name__,m.__version__) for m in (numpy,pandas,scipy,matplotlib,uproot)]"
# (8) ROOPY 版本
ls /junofs/users/shubingliu/uv_envs/ROOPY/lib/python3.12/site-packages/ | grep dist-info | grep -E "numpy|pandas|scipy|matplotlib|uproot|awkward|numba|tqdm|psutil|reconstruction"
```
