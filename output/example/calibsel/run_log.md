# Run Log — standalone_esd2npz (schema 2.0)

**Run ID**: `20260825T170131_d541ae`  |  **Status**: `completed`  |  **Elapsed**: 238.23 s

**Command**: `run_all.py --out-dir /datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz --runs 12370`

**Exit code**: `0`

## System Information

| Field | Value |
|---|---|
| hostname | `user-Super-Server` |
| user | `lin` |
| platform | `Linux-6.8.0-136-generic-x86_64-with-glibc2.39` |
| python_version | `3.12.3` |
| python_executable | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/.venv/bin/python` |
| timestamp_utc | `2026-08-25T09:01:31.513719+00:00` |

## Code Version

| Field | Value |
|---|---|
| Git commit | `3173d71316274f19c8904c68d5a52f49ac16afbc` |
| Git branch | `main` |
| Git has_uncommitted_changes | `True` |

> Warning: Working tree has uncommitted changes.

## Package Versions

- **numpy**: `2.5.2`
- **pandas**: `3.0.5`
- **scipy**: `1.18.1`
- **matplotlib**: `3.11.1`
- **uproot**: `5.7.6`

## Configuration Files

| Config | Path | SHA-256 |
|---|---|---|
| config/paths.py | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/config/paths.py` | `64eb1f8f42d4df00...` |
| requirements.txt | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/requirements.txt` | `06bd0e0e1cbed278...` |
| calib_run_info/calib_to_analyze.txt | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/calib_run_info/calib_to_analyze.txt` | `6cad458da25b8d43...` |
| calib_run_info/CalibRUN_from_file.csv | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/calib_run_info/CalibRUN_from_file.csv` | `84d39f499b8b560a...` |
| input/correction/correction_api.py | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/esd2npz/input/correction/correction_api.py` | `500d1f45200db7f2...` |

## Pipeline

- **mode**: `from-edm`
- **runs**: `[12370]`
- **edm_input**: `auto`
- **remote_edm_dir**: `/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data`
- **slice**: `None`
- **skip_bkg**: `False`

## Audit (end-of-run completeness)

| Check | Result |
|---|---|
| code/ snapshot files | `41` |
| code all sha256 match | `True` |
| outputs all present | `True` |
| **audit passed** | **`True`** |

## Per-Run Records


### [OK] RUN12419 — bkg-of-12370

| Field | Value |
|---|---|
| Status | ok |
| EDM dir | `/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data` |
| EDM chunks | `7` |
| Events (total / finite) | `2766750 / 2766750` |
| Energy min/max | `-999.0 / 64.24397277832031 MeV` |
| Energy mean/median | `-803.3070719880483 / -999.0 MeV` |

| stage | status | seconds | detail |
|---|---|---|---|
| 1 edm->npz | ok | 100.8 | edm_dir=/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data; n_chunks=7 |
| 2 finalcorrection | ok | 4.4 | phase=3; absolute_scale=0.99743135 |

| output | kind | sha256 |
|---|---|---|
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/npz_raw/RUN12419.npz` | npz_raw | `22fcdc9c52e10672...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/npz_corrected/RUN12419.npz` | npz_corrected | `8f5c73a6fbf806f8...` |

### [OK] RUN12370 — Ge68

| Field | Value |
|---|---|
| Status | ok |
| run | `12370` |
| source | `Ge68` |
| date | `2025-12-17` |
| x_m | `0.0` |
| y_m | `0.0` |
| z_m | `0.0` |
| r_m | `0.0` |
| EDM dir | `/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data` |
| EDM chunks | `8` |
| Events (total / finite) | `1492630 / 1492630` |
| Energy min/max | `-999.0 / 58.23025131225586 MeV` |
| Energy mean/median | `-25.083794602204605 / 0.34133563935756683 MeV` |
| Cuts | `cuts/12370_cuts.json` |

| stage | status | seconds | detail |
|---|---|---|---|
| 1 edm->npz | ok | 98.8 | edm_dir=/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data; n_chunks=8 |
| 2 finalcorrection | ok | 3.3 | phase=3; absolute_scale=0.99743135 |
| 3 selection | ok | 21.2 | cuts_file=cuts/12370_cuts.json |
| 4 physics-qa | ok | 4.8 |  |

| output | kind | sha256 |
|---|---|---|
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/npz_raw/RUN12370.npz` | npz_raw | `193e9091449e7c45...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/npz_corrected/RUN12370.npz` | npz_corrected | `1ac0c20f1ed0a755...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/timestamps/Timestamp_wo_Ecut/RUN12370.txt` | selection Timestamp_wo_Ecut/RUN12370.txt | `ac4e729fa6dc5930...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_EnergySpectrum.png` | selection figrues_check/Run12370_EnergySpectrum.png | `53eced9ad6b9ddd7...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_Rho_vs_Z.png` | selection figrues_check/Run12370_Rho_vs_Z.png | `b7440505d4f12385...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_Rho_vs_Z_EFV.png` | selection figrues_check/Run12370_Rho_vs_Z_EFV.png | `8263dc0e4e245acf...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_EnergySpectrum_Selection.png` | selection figrues_check/Run12370_EnergySpectrum_Selection.png | `10b399b74c19eea5...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/timestamps/Timestamp_Ecut/RUN12370.txt` | selection Timestamp_Ecut/RUN12370.txt | `8d0d1e1fef4f4ee9...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_2_EnergySpectrum_Fit.png` | selection figures_check_important_new/Run12370_2_EnergySpectrum_Fit.png | `c8f4c4ac3ef3bd41...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/selection/Run12370_1_SelectionPlot.png` | selection figures_check_important_new/Run12370_1_SelectionPlot.png | `63425be27de00743...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run12370_SelectionResult.npz` | selection npz/Run12370_SelectionResult.npz | `875b1662638ca16a...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/physics_qa/Run12370_physics_qa.png` | physics_qa | `1bda1b4cf9b13201...` |
| `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/figures/physics_qa/Run12370_physics_qa.json` | physics_qa_json | `4acaffc932841412...` |

See `code_snapshot/sha256.json` for the exact algorithm versions (cut logic) used by this run, and `cuts/` for the run-specific selection conditions.
