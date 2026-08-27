# Skill: Running the Pipeline — standalone_calibsel

## Description

How to execute the pipeline for one or many runs, in default (from-EDM) or
full-ESD mode, and how to read the output directory. Use this skill for
production processing and smoke tests.

---

## Quick Start (default: from pre-existing EDM)

```bash
cd standalone_calibsel
bash run_pipeline.sh                 # DEFAULT_RUNS (12370), from-edm mode
bash run_pipeline.sh 12370 12295     # explicit runs
bash run_pipeline.sh --skip-qa       # without the QA figure stage
```

One command creates the venv if missing, then runs
`pipeline/run_all.py`. Typical time in from-edm mode:
**~2–4 min per run** (dominated by reading EDM chunks over lustrefs).

Direct python equivalent:

```bash
.venv/bin/python pipeline/run_all.py --runs 12370
```

## Full-ESD Mode (local ESD→EDM reconstruction)

```bash
bash run_pipeline.sh 12370 --full-esd              # whole run (~hours)
bash run_pipeline.sh 12370 --full-esd --slice 3    # smoke test, 3 ESD files
```

Requires the external JUNO environment (skill 02). Note: chunks rebuilt with
the current (June) JUNOSW build differ microscopically from the May reference
in `totalPE` only (~2e-4 median; not used downstream) — all other branches
are bitwise identical (skill 10).

## What Each Stage Does

| Stage | Script | Output |
|---|---|---|
| 0a/0b (opt.) | `src/list_esd.py`, `src/esd_to_edm.py` | `data/edm/run_{R}_{i}_{j}.root` |
| 1 | `src/convert_edm_to_npz.py` | `results/npz_raw/RUN{R}.npz` |
| 2 | `src/apply_final_correction.py` | `results/npz_corrected/RUN{R}.npz` |
| 2b | auto (stages 1–2) for the mapped background run | `results/npz_corrected/RUN{bkg}.npz` |
| 3 | `src/combine_selection.py` | `results/selection_npz/Run{R}_SelectionResult.npz` + timestamps + figures |
| 4 | `tools/make_physics_qa.py` | `figures/physics_qa/Run{R}_physics_qa.png` |

The background run (Stage 2b) is resolved from
`calib_run_info/calib_to_analyze.txt` and skipped automatically if its
corrected NPZ already exists in this output directory. Use `--skip-bkg` to
disable.

## Useful Flags

| Flag | Effect |
|---|---|
| `--runs 12370 12295` | process these runs (default: `DEFAULT_RUNS`) |
| `--full-esd` | also reconstruct ESD→EDM locally |
| `--slice N` | with `--full-esd`: only first N ESD files (smoke test) |
| `--edm-input DIR` | custom EDM chunk directory (e.g. your own rebuild) |
| `--skip-bkg` | do not auto-process the background run |
| `--skip-qa` | skip the physics QA figure stage |
| `--launched-by agent` | mark the run log as agent-driven |

## After the Run

- Check `run_log.md` first: system/git/package versions, config fingerprints,
  per-run records (run_info, event statistics, input/output SHA-256, stage
  status/elapsed), errors[] and exit code.
- Check the **Audit** section of `run_log.md` (or `run_log.json -> audit`):
  every run ends with a completeness audit — the complete code tree copied to
  `output/<ts>/code/` (with `code/sha256.json`) is verified byte-identical to
  the working tree, and every deliverable (run_log, config_snapshot, cuts,
  selection NPZ, npz_raw/npz_corrected, figures) must exist.
  - `[AUDIT] PASSED` → results are trustworthy; `output/latest` was published.
  - `[AUDIT] FAILED` (script mode) → pipeline **exited with code 3**, no
    `latest` publish; investigate the missing/mismatched lists before use.
  - `[AUDIT] WARNING` (agent mode) → audit failed but the pipeline continued;
    the agent must state this in its report (run_log status = `audit-failed`).
- Check `cuts/summary.md` for the selection conditions of every run (skill 07).
- Open `figures/physics_qa/Run{R}_physics_qa.png` for the physics check (skill 08).
- Hand-off to the fitter: `output/latest` is atomically repointed to this
  run's directory on success, so a fitter configured once with
  `DATA_INPUT_PATH = <project>/output/latest/results/selection_npz` picks up
  every new batch automatically (see skill 09 for the exact snippet).

## Manual Single-Stage Runs (advanced)

Each stage script keeps its own CLI and can be run directly; outputs default
to the legacy `data/` tree:

```bash
.venv/bin/python src/convert_edm_to_npz.py --run 12370 --input-dir <EDM>
.venv/bin/python src/apply_final_correction.py 12370 --input <npz> --out-dir <dir>
.venv/bin/python src/combine_selection.py 12370 --Finalcorrection \
    --input-dir <corrected> --out-dir <workdir>
```

Prefer the orchestrator for anything that must be archived: manual runs do
not create run_log / cuts / code_snapshot records.
