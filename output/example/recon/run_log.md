# Run Log — standalone_calibsel (schema 2.0)

**Run ID**: `20260828T002003_88eaba`  |  **Status**: `completed`  |  **Elapsed**: 64.9 s

**Command**: `run_recon_all.py --runs 10110 --impl omilrecv2 --slice 1 --evtmax 100 --out-dir /datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260828_recon_smoke/recon`

**Exit code**: `0`

## System Information

| Field | Value |
|---|---|
| hostname | `user-Super-Server` |
| user | `wujxy` |
| platform | `Linux-6.8.0-136-generic-x86_64-with-glibc2.34` |
| python_version | `3.11.10` |
| python_executable | `/datafs/users/wujxy/py_venv/alma/juno_env/bin/python3` |
| timestamp_utc | `2026-08-27T16:20:03.934033+00:00` |

## Code Version

| Field | Value |
|---|---|
| Git commit | `e1d98d153c7d1ed52b097c2b0f42198b0d8592fd` |
| Git branch | `main` |
| Git has_uncommitted_changes | `True` |

> Warning: Working tree has uncommitted changes.

## Package Versions

- **numpy**: `2.4.6`
- **pandas**: `not-installed`
- **scipy**: `not-installed`
- **matplotlib**: `3.11.1`
- **uproot**: `not-installed`

## Configuration Files

| Config | Path | SHA-256 |
|---|---|---|
| config/paths.py | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/recon/config/paths.py` | `522b26da06a791cb...` |
| requirements.txt | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/recon/requirements.txt` | `n/a...` |
| calib_run_info/calib_to_analyze.txt | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/recon/calib_run_info/calib_to_analyze.txt` | `n/a...` |
| calib_run_info/CalibRUN_from_file.csv | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/recon/calib_run_info/CalibRUN_from_file.csv` | `n/a...` |
| input/correction/correction_api.py | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/recon/input/correction/correction_api.py` | `n/a...` |

## Pipeline

- **impl**: `omilrecv2`
- **runs**: `[10110]`
- **slice**: `1`
- **evtmax**: `100`
- **global_tag**: `ReProd26A_v1`
- **omilrecv2_dir**: `/datafs/users/wujxy/agent-sci/omilrec_opt/omilrecv2`
- **maps_dir**: `/data/juno/dingxf/OMILREC_maps`

## Audit (end-of-run completeness)

| Check | Result |
|---|---|
| code/ snapshot files | `6` |
| code all sha256 match | `True` |
| outputs all present | `True` |
| **audit passed** | **`True`** |

## Per-Run Records


### [OK] RUN10110 — AmC117

| Field | Value |
|---|---|
| Status | ok |
| RUN | `10110` |
| Date | `2025-09-12` |
| X[m] | `0.0` |
| Y[m] | `0.0` |
| Z[m] | `0.0` |
| Source | `AmC117` |
| R[m] | `0.0` |

| stage | status | seconds | detail |
|---|---|---|---|
| -1pre verify-maps | ok | 1.339850902557373 | n_assets=4; problems=[] |
| -1a rtraw-list | ok | 0.3406045436859131 | n_files=1 |
| -1b rtraw->esd | ok | 63.2107629776001 | esd_root=/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260828_recon_smoke/recon/results/esd/RUN10110/recon_RUN10110.root; evtmax=100 |
| handoff esd-list | ok | 0.0 | esd_list=/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260828_recon_smoke/recon/results/esd_lists/esd_list_10110.txt |

| output | kind | sha256 |
|---|---|---|
| `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260828_recon_smoke/recon/results/esd/RUN10110/recon_RUN10110.root` | esd_root | `n/a...` |
| `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260828_recon_smoke/recon/results/esd_lists/esd_list_10110.txt` | esd_list_handoff | `n/a...` |

See `code_snapshot/sha256.json` for the exact algorithm versions (cut logic) used by this run, and `cuts/` for the run-specific selection conditions.
