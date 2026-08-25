# Skill: Selection Cuts & Run Archiving (留档) — the most important skill

## Description

How the selection conditions are preserved for every run: what cuts exist,
where their values are archived, and how to read them back. **This is the
core record-keeping skill of the project** — any published number must be
traceable to a `cuts/{R}_cuts.json`.

---

## Two Layers of Cut Provenance

### 1. Runtime cut values — `output/<ts>/cuts/{R}_cuts.json`

Written automatically by `pipeline/cuts_parser.py` from the actual
combine_selection console output of this run. Example (RUN 12370, Ge68):

```json
{
 "run": 12370, "source": "Ge68", "bkg_run": 12419,
 "ROI_MeV": [0.46, 1.23],
 "step1_energy_region_MeV": [0.465, 0.685],
 "z_cut": {"RD_threshold_percent": 0.08, "z_limit_m": 0.4185},
 "z_expected_m": 0.001, "z_source_true_m": 0.0,
 "calib_muonveto_kept": {"kept": 1413255, "total": 1492630, "percent": 94.68},
 "bkg_muonveto_kept":   {"kept": 2612627, "total": 2766750, "percent": 94.43},
 "EFV_selected": {"kept": 109212, "input": 1413255},
 "final_energy_cut_MeV": [0.4945, 0.74526],
 "events_after_ecut": 17407,
 "static_cut_definitions": { ... }
}
```

`cuts/summary.md` accumulates one table row per run for quick multi-run
comparison of cut stability.

### 2. Static cut logic — `code_snapshot/` + `sha256.json`

The hard-coded scan constants (also embedded in the JSON under
`static_cut_definitions` for readability):

| Constant | Value | Meaning |
|---|---|---|
| nominal energies | Ge68 1.022, Cs137 0.662, Mn54 0.835, K40 1.461, Co60 2.506, nH/AmC 2.223, nC 4.94, O16 6.13 MeV | seeds the ROI scan |
| `SOURCE_INITIAL_ROI_SCALE` | Ge68 (0.45, 1.20) MeV | robust initial ROI for edge sources |
| `FIT_LOW/HIGH_SCALE` | 0.9 / 1.1 | final fit window × Step-1 region |
| `FIT_BIN_WIDTH` | 0.002 MeV | fit histogram binning |
| EFV ellipse | `sqrt((ρ/ρ_limit)² + ((z−z_exp)/z_limit)²) ≤ 1` | ρ_limit & z_limit from the robust scan |
| z pre-exclusion | `|z| ≥ 17.7 m` dropped | |
| MuonVeto | keep `MuonVeto == False` | |
| energy cut | `μ ± 3σ` of the fitted peak | σ from Gaussian+poly fit on Step-1 region |

The verbatim `src/combine_selection.py` that produced the cuts is copied into
`output/<ts>/code_snapshot/src/combine_selection.py`, with its sha256 in
`code_snapshot/sha256.json` — the authoritative definition of the cut
algorithm for that run.

## How the Robust Scan Decides the Runtime Values

1. **ROI**: initial window from nominal energy (or `SOURCE_INITIAL_ROI_SCALE`),
   then mu±nσ grid scan with quadratic+Gaussian fits → most stable region
2. **Step-1 energy region**: the robust sub-region used for vertex studies
3. **z_limit**: walking z until the relative derivative drops below the
   0.08 % threshold, confirmed by a 5-point robustness check
4. **ρ_limit / EFV**: ellipse in (ρ, z−z_exp) space with the scanned limits
5. **final energy cut**: Gaussian fit on the Step-1 spectrum → μ±3σ window;
   timestamp files are written with (`Timestamp_Ecut`) and without
   (`Timestamp_wo_Ecut`) this energy cut

## Run Log (audit-grade, mirrors standalone_fitter, schema 2.0)

`output/<ts>/run_log.{md,json}` 与 `config_snapshot.json` 提供与 fitter 对齐的审计链：

**pipeline_metadata（run_log.json 顶层）**：

| 类别 | 字段 |
|---|---|
| 启动 | `launched_by`、`command[]`、`exit_code`、`run_id` |
| 时间 | `timestamp_start/end_utc` + `timestamp_start/end_local`（双格式） |
| 系统 | hostname、user、platform、python_version、**python_executable** |
| 代码版本 | `git`：commit、branch、has_uncommitted_changes |
| 依赖 | `packages`（numpy/pandas/scipy/matplotlib/uproot 版本）+ **`pip_freeze`（完整清单）** |
| 配置指纹 | `config_files` + `config_snapshot`：paths.py / requirements.txt / calib 两表 / correction_api.py 的 **路径+SHA-256+大小** |
| 错误 | `errors[]`：结构化（时间戳/来源/消息） |
| 流水线 | mode、runs、EDM 目录、slice、latest 发布链接 |

**runs[]（每个 run（含本底 run）一条，镜像 fitter 的 sources[]）**：

| 字段 | 内容 |
|---|---|
| `run_info` | 日期、源、位置 X/Y/Z、R（来自 CalibRUN_from_file.csv） |
| `input` | EDM 目录、分块数、raw npz 的**路径+大小+SHA-256** |
| `event_statistics` | 总事件/有限值事件数、能量 min/max/mean/median、**200-bin 预选择谱直方图**（可重建输入分布） |
| `stages` | 每阶段状态/耗时/细节（含 phase、absolute_scale、n_chunks） |
| `cuts_ref` | 指向 `cuts/{RUN}_cuts.json` |
| `outputs` | 每个产出文件的**路径+大小+SHA-256**（npz/时间戳/图/QA） |

- `config_snapshot.json`：上述配置文件的完整指纹（路径+SHA-256+大小）
- `code/`（完整代码快照）：每次运行结束时把**整个代码树**（src/pipeline/tools/config/skills/input/calib_run_info/lib + 根文件，排除 .venv/data/output/TMP 等运行产物）复制到 `code/`，附 `code/sha256.json`——运行该批数据所用的**全部代码的逐字节档案**
- `code_snapshot/` + `sha256.json`：算法文件权威指纹（cut 逻辑，精简子集）
- `console.log` + `logs/stage*.log`：完整阶段输出
- `traceback.log`：未处理异常时自动生成，status=failed
- 失败运行仍完整落盘：已完成的 run 记录保留，`errors[]` 记录失败 stage

**Audit（结束完整性审计，run_log.json -> audit + run_log.md -> Audit）**：

| 检查 | 含义 |
|---|---|
| `code_snapshot.all_match` | `code/` 内每个文件与工作树**物理存在且 sha256 逐字节一致**（missing/mismatched/extra 三清单为空） |
| `outputs.all_present` | 全部关键产物存在：run_log、config_snapshot、console.log、`code/sha256.json`、每 run 的 cuts json、selection NPZ、npz_raw/npz_corrected、selection 图 |
| `passed` | 两者皆真 |

失败处置：script 模式打印 `[AUDIT] FAILED` 并 **exit 3**（不发布 `latest`）；agent 模式打印 `[AUDIT] WARNING`（run_log status=`audit-failed`），agent 必须在汇报中明示。

**第三方复核路径**：取 `run_log.json` → 按 git commit 检出代码 → 按 config_snapshot 校验配置 → 按 SHA-256 校验输入 npz/输出文件 → 复核事件统计与 cuts 值 → 对照 `logs/stage*.log` 过程。

## Reading Cuts Back Later

```bash
# one run
python -c "import json;print(json.load(open('cuts/12370_cuts.json'))['final_energy_cut_MeV'])"
# all runs
column -t -s'|' cuts/summary.md
```

If you are comparing two processing epochs, diff both the `cuts/*.json`
(values) and `code_snapshot/sha256.json` (logic) — identical hashes with
different values mean input data changed; different hashes mean the cut code
itself changed and results are not comparable without re-audit.
