# Skill: Troubleshooting — common failures and fixes

## Description

Symptom → cause → fix for the most frequent problems. Use this skill when a
pipeline run fails or output looks wrong.

---

## Stage 0 (`--full-esd` only)

| Symptom | Cause | Fix |
|---|---|---|
| `[3010] Opening relative path ... is disallowed` | single-slash xrootd URL | use `src/list_esd.py` output (double slash); don't hand-write the list |
| `libpcre.so.1: cannot open shared object` | host lacks PCRE1 | re-run `bash setup_env.sh` (copies it into `lib/`) |
| `GLIBCXX_3.4.29 not found` | whole anaconda lib dir in `LD_LIBRARY_PATH` | only `lib/` (single file) may be prepended — the wrapper does this; don't "fix" it by adding more |
| xrdfs "command not found" / plugin errors | CVMFS env not captured | `src/list_esd.py` sources the CVMFS setup itself; if it still fails check `/cvmfs` is mounted |
| reconstruction very slow | full run = 147 ESD × ~5 min | use `--slice 3` for smoke tests |

## Stage 1 (EDM → NPZ)

| Symptom | Cause | Fix |
|---|---|---|
| `No EDM ROOT files found for RUN R` | run not in `REMOTE_EDM_DIR` | check `ls $REMOTE_EDM_DIR | grep run_{R}`; pass `--edm-input DIR` for custom chunks |
| lustrefs reads time out | network hiccup | retry; keep runs per invocation small if flaky |
| Entries = 0 | empty/garbage chunks | inspect `logs/stage1_{R}.log` for per-file read errors |

## Stage 2 (correction)

| Symptom | Cause | Fix |
|---|---|---|
| `phase` unexpected | run outside phase table | check `ValProd26BPhase.csv` coverage; runs before ReProd26B are out of scope |
| outputs differ from reference | correction data edited | `input/correction/*` must be the md5-verified copies (skill 05) |

## Stage 3 (selection)

| Symptom | Cause | Fix |
|---|---|---|
| `Error: Config file not found` | ran outside project root | call via `pipeline/run_all.py` or `cd` into the project |
| source unresolved / `None` | run not in `calib_to_analyze.txt` | add the range (frozen copy — document the change!) or use a mapped run |
| `fitted_peaks == []` in QA JSON | spectrum anomaly (real physics issue) | inspect panel A/B; check input EDM for that run |

## Stage 4 (QA)

Matplotlib cache warnings are harmless (`MPLCONFIGDIR` is set automatically).
A failed QA stage never fails the pipeline.

## Output / hand-off

| Symptom | Cause | Fix |
|---|---|---|
| fitter skips a run | `SelectionResult.npz` missing | selection stage failed — see `logs/stage3_{R}.log` and `run_log.md` |
| fitter uses stale data | its `DATA_INPUT_PATH` points elsewhere | point it at `output/latest/results/selection_npz` (auto-follows every successful batch); for a frozen epoch use the explicit `output/<ts>/` path |

## Verifying a suspicious result

1. `run_log.md` → any stage failed?
2. `cuts/{R}_cuts.json` → do the cut values look sane vs `cuts/summary.md` of
   earlier runs?
3. `figures/physics_qa/Run{R}_physics_qa.png` → panel-by-panel check (skill 08)
4. bitwise audit against the reference chain if the run is 12370-like
   (skill 10)
