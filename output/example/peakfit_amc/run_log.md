# Run Log — JUNO Calibration Fitter Pipeline (v2.0)

**Run ID**: `20260827T203930_98568280`
**Status**: `completed`
**Launched by**: `script`
**Start (UTC)**: 2026-08-27T12:39:30.812314Z
**End (UTC)**:   2026-08-27T12:41:29.528304Z

**Command**: `pipeline/run_amc_fit_all.py --run 10110 --corr-npz /datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/amcsel/results/RUN10110/correlation_result_RUN10110.npz --out-dir /datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc`
**Exit code**: `0`

## System Information

| Field | Value |
|-------|-------|
| Hostname | `user-Super-Server` |
| User | `wujxy` |
| Platform | `Linux-6.8.0-136-generic-x86_64-with-glibc2.34` |
| Python | `3.11.10` |

## Code Version

| Field | Value |
|-------|-------|
| Git commit | `f3083632cd8f84d16d36842629bfe5266318f181` |
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
| paths_py | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/fitter/config/paths.py` | `aa272c242f264da7...` |
| calib_run_csv | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/fitter/CalibRUN.csv` | `84d39f499b8b560a...` |
| requirements_txt | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/fitter/requirements.txt` | `0351e588f90a087a...` |

---
## Per-Source Records

### [OK] nH — RUN10110

| Field | Value |
|-------|-------|
| Status | success |
| Source | nH |
| Run | 10110 |
| Date | 2025-09-12 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 2.2233 MeV |
| Fitter | `gaussian` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/amcsel/results/RUN10110/correlation_result_RUN10110.npz` |
| Size | 1,874,716 bytes |
| SHA-256 | `ab2b13440ec425ad...` |

#### Fit Results

| Field | Value |
|-------|-------|
| Mu | 2.2193 MeV |
| Sigma/E | 2.58% |
| Chi2/ndf | 69.7/73 |
| Time | 0.3s |

#### Output Files

- **result_npz**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/results/RUN10110_nH.npz` (SHA-256: `1772a18a8683...`)
- **figure**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/figures/RUN10110_nH.png` (SHA-256: `912ae9688028...`)

### [OK] nC — RUN10110

| Field | Value |
|-------|-------|
| Status | success |
| Source | nC |
| Run | 10110 |
| Date | 2025-09-12 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 4.9500 MeV |
| Fitter | `gaussian` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/amcsel/results/RUN10110/correlation_result_RUN10110.npz` |
| Size | 1,874,716 bytes |
| SHA-256 | `ab2b13440ec425ad...` |

#### Fit Results

| Field | Value |
|-------|-------|
| Mu | 5.0239 MeV |
| Sigma/E | 2.27% |
| Chi2/ndf | 94.4/71 |
| Time | 0.3s |

#### Output Files

- **result_npz**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/results/RUN10110_nC.npz` (SHA-256: `739ed3036dcd...`)
- **figure**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/figures/RUN10110_nC.png` (SHA-256: `66f079a7bafe...`)

### [OK] AmC — RUN10110

| Field | Value |
|-------|-------|
| Status | success |
| Source | AmC |
| Run | 10110 |
| Date | 2025-09-12 |
| Position | (0.0, 0.0, 0.0) m |
| E_true | 6.1290 MeV |
| Fitter | `o16-template` |

#### Input Data

| Field | Value |
|-------|-------|
| File | `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/amcsel/results/RUN10110/correlation_result_RUN10110.npz` |
| Size | 1,874,716 bytes |
| SHA-256 | `ab2b13440ec425ad...` |

#### Fit Results

| Field | Value |
|-------|-------|
| Mu | 6.3023 MeV |
| Sigma/E | 1.59% |
| Chi2/ndf | 1370.8/21 |
| Time | 116.8s |

#### Output Files

- **result_npz**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/results/RUN10110_AmC.npz` (SHA-256: `20b125c87688...`)
- **figure**: `/datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/fitter_amc/figures/RUN10110_AmC.pdf` (SHA-256: `3960ac956a38...`)

---
## Summary

| Field | Value |
|-------|-------|
| run | 10110 |
| peaks | ['nH', 'nC', 'AmC'] |
| corr_npz | /datafs/users/wujxy/agent-sci/juno-acu-energy-calibration-pipeline/output/20260827_203916/amcsel/results/RUN10110/correlation_result_RUN10110.npz |

---
## Audit (end-of-run completeness)

| Check | Result |
|-------|--------|
| code/ snapshot files | `54` |
| code all sha256 match | `True` |
| outputs all present | `True` |
| log files all present | `True` |
| **audit passed** | **`True`** |

---
*End of run log*
