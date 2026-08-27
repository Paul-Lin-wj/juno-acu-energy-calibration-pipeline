# Run Log — JUNO Calibration Fitter Pipeline (v2.0)

**Run ID**: `20260825T170534_3b518cb3`
**Status**: `completed`
**Launched by**: `script`
**Start (UTC)**: 2026-08-25T09:05:34.606562Z
**End (UTC)**:   2026-08-25T09:05:40.725338Z

**Command**: `pipeline/run_fit_all.py --input-dir /datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz --out-dir /datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/fitter`
**Exit code**: `0`

## System Information

| Field | Value |
|-------|-------|
| Hostname | `user-Super-Server` |
| User | `lin` |
| Platform | `Linux-6.8.0-136-generic-x86_64-with-glibc2.39` |
| Python | `3.12.3` |

## Code Version

| Field | Value |
|-------|-------|
| Git commit | `3173d71316274f19c8904c68d5a52f49ac16afbc` |
| Git branch | `main` |
| Uncommitted changes | `True` |

> Warning: Working tree has uncommitted changes.

## Package Versions

- **numpy**: `1.26.4`
- **scipy**: `1.13.1`
- **matplotlib**: `3.9.0`
- **iminuit**: `2.30.1`
- **pandas**: `2.2.2`

## Configuration Files

| Config | Path | SHA-256 |
|-------|------|--------|
| paths_py | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/fitter/config/paths.py` | `aa272c242f264da7...` |
| calib_run_csv | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/fitter/CalibRUN.csv` | `84d39f499b8b560a...` |
| requirements_txt | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/fitter/requirements.txt` | `0351e588f90a087a...` |

---
## Per-Source Records

### [OK] Ge68 — RUN12370

| Field | Value |
|-------|-------|
| Status | success |
| Source | Ge68 |
| Run | 12370 |
| Date | 2025-12-17 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 0.8845 MeV |
| Fitter | `fast` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run12370_SelectionResult.npz` |
| Size | 2,622,422 bytes |
| SHA-256 | `875b1662638ca16a...` |

#### Events

| Field | Value |
|-------|-------|
| Total | 109212 |
| Energy range | 0.0000 - 11.6899 MeV |

#### Fit Results

| Field | Value |
|-------|-------|
| Mu | 0.9102 MeV |
| Sigma/E | 3.54% |
| Chi2/ndf | 600.2/358 |
| Time | 3.4s |

#### Output Files

- **result_npz**: `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/fitter/results/RUN12370_Ge68.npz` (SHA-256: `3836808bec51...`)
- **figure**: `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/fitter/figures/RUN12370_Ge68.pdf` (SHA-256: `12f9a4c62fa9...`)

### [SKIP] Cs137 — RUN12295

| Field | Value |
|-------|-------|
| Status | skipped |
| Source | Cs137 |
| Run | 12295 |
| Date | 2025-12-16 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 0.6620 MeV |
| Fitter | `fast` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run12295_SelectionResult.npz` |
| Size | 0 bytes |
| SHA-256 | `...` |

### [SKIP] Mn54 — RUN12247

| Field | Value |
|-------|-------|
| Status | skipped |
| Source | Mn54 |
| Run | 12247 |
| Date | 2025-12-15 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 0.8350 MeV |
| Fitter | `fast` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run12247_SelectionResult.npz` |
| Size | 0 bytes |
| SHA-256 | `...` |

### [SKIP] Co60 — RUN12216

| Field | Value |
|-------|-------|
| Status | skipped |
| Source | Co60 |
| Run | 12216 |
| Date | 2025-12-15 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 2.5060 MeV |
| Fitter | `fast` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run12216_SelectionResult.npz` |
| Size | 0 bytes |
| SHA-256 | `...` |

### [SKIP] K40 — RUN9632

| Field | Value |
|-------|-------|
| Status | skipped |
| Source | K40 |
| Run | 9632 |
| Date | 2025-08-25 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 1.4610 MeV |
| Fitter | `fast` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/esd2npz/results/selection_npz/Run9632_SelectionResult.npz` |
| Size | 0 bytes |
| SHA-256 | `...` |

---
## Summary

| Field | Value |
|-------|-------|
| total_sources_configured | 5 |
| total_sources_fitted | 1 |
| total_time_s | 3.9 |
| sources | Ge68 |
| output_directory | /datafs/users/lin/workplace/energy_reco/ENL_agent/calib_pipeline_suite/output/20260825_170131/fitter |

---
## Audit (end-of-run completeness)

| Check | Result |
|-------|--------|
| code/ snapshot files | `52` |
| code all sha256 match | `True` |
| outputs all present | `True` |
| log files all present | `True` |
| **audit passed** | **`True`** |

---
*End of run log*
