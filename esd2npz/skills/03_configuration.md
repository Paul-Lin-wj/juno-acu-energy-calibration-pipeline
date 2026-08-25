# Skill: Configuration — standalone_esd2npz

## Description

Everything configurable lives in **one file**: `config/paths.py`. Use this
skill when moving to a new machine, changing the default runs, switching
input datasets, or adjusting output locations.

---

## The Only File You Normally Edit: `config/paths.py`

### Default mode & runs

```python
DEFAULT_MODE = "from-edm"     # "from-edm" (= old --skip-esd) | "full-esd"
DEFAULT_RUNS = [12370]        # runs processed when none are given
```

`"from-edm"` starts from the pre-existing ReProd26B EDM chunks
(`REMOTE_EDM_DIR`) — **no external JUNO environment needed**. `"full-esd"`
additionally reconstructs ESD→EDM locally (CVMFS + JUNOSW + EOS required).
CLI flags override: `--full-esd` forces the reconstruction mode for one run.

### Input locations

| Setting | Meaning |
|---|---|
| `REMOTE_EDM_DIR` | pre-existing EDM chunks (default input of stage 1 in `from-edm` mode) |
| `ESD_BASE`, `XROOTD_HOST` | EOS ESD tree + xrootd host (only for `--full-esd`) |
| `CVMFS_SETUP`, `JUNOSW_SETUP`, `RUN_PY` | JUNO software paths (only for `--full-esd`) |

### Output layout (standard, mirrors standalone_fitter)

```
output/<YYYYmmdd_HHMMSS>/
├── results/
│   ├── npz_raw/RUN{R}.npz                  # stage 1 output
│   ├── npz_corrected/RUN{R}.npz            # stage 2 output (+ bkg run)
│   ├── selection_npz/Run{R}_SelectionResult.npz   # ★ fitter input
│   └── timestamps/Timestamp_{wo,E}cut/RUN{R}.txt
├── figures/
│   ├── selection/*.png                     # selection QA plots from stage 3
│   └── physics_qa/Run{R}_physics_qa.{png,json}
├── cuts/{R}_cuts.json, summary.md          # ★ selection conditions archive
├── logs/stage*.log                         # full per-stage console logs
├── code_snapshot/                          # verbatim algorithm files + sha256
├── run_log.md / run_log.json               # audit-grade run record
├── config_snapshot.json                    # every tunable used by this run
└── console.log                             # complete console output
```

`OUTPUT_DIR` (default `output/`) can be redirected, e.g. to a scratch disk.

### The `output/latest` auto-publish convention

On every **fully successful** run the orchestrator atomically repoints the
symlink `output/latest` at the new timestamp directory (a `publish` stage
row appears in `run_log.md`). Failed runs never touch it, so `latest` always
refers to a complete dataset. Downstream consumers (the fitter) should point
at the stable path:

```
<project>/output/latest/results/selection_npz
```

configured **once** — no per-batch path updates are needed.

### Legacy directories

`data/npz_raw`, `data/npz_corrected`, `data/selection` remain the fallback
defaults for **manual** `src/*.py` invocations. The orchestrated pipeline
always writes into `output/<timestamp>/`; the legacy `data/` tree is never
touched by `run_all.py`.

## Correction Data (do not edit)

`input/correction/` holds `correction_api.py` plus the 7 model files
(phase1–4 npz, time/vertex/phase CSVs, 212 KB). These are **md5-verified
copies** of the original chain's correction inputs (see `PROVENANCE.md`) —
modifying them silently changes the physics. If a new correction model is
released, replace the whole set and re-run the bitwise audit (skill 10).

## Run→source/background mapping

`calib_run_info/calib_to_analyze.txt` maps run ranges to source and physics
(background) run; `CalibRUN_from_file.csv` gives run date/vertex/source
position. Both are frozen copies of the original chain. Stage 2b reads this
mapping to auto-process the background run.
