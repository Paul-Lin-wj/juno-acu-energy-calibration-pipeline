# JUNO ACU Energy Nonlinearity Calibration Pipeline

[中文版](README.md)

## Overview

End-to-end processing pipeline for JUNO (Jiangmen Underground Neutrino
Observatory) ACU (Automatic Calibration Unit) gamma-source calibration data:
from raw reconstruction output to **energy spectrum fitting results**
(peak position μ, resolution σ/E), covering five single-event calibration
sources — Ge68 / Cs137 / Mn54 / Co60 / K40.

```
ESD / EDM (raw reconstructed data)
   │  esd2npz/
   ▼
NPZ (per-run merged events + LivingTime)
   │  26B Finalcorrection (r-bias vertex + spatial + time + phase absolute scale)
   ▼
corrected NPZ
   │  selection: MuonVeto → robust ROI → Z-cut → EFV ellipse → energy window
   ▼
Run{N}_SelectionResult.npz (fitter input)
   │  fitter/
   ▼
fitting: MC template convolution + Minuit → μ / σ / χ² + ENL resolution plot
```

Every step's selection conditions (ROI, z_limit, energy window, ...) are
archived with the run; each run also ships a **complete code snapshot** and an
**end-of-run completeness audit**, so results are fully traceable.

## Repository Layout

| Path | Purpose |
|---|---|
| `esd2npz/` | Data-processing pipeline: EDM→NPZ→26B correction→selection. `src/` is the algorithm code (line-by-line port of the original production chain; outputs bitwise identical to it); `pipeline/` holds orchestration & audit logging; `input/correction/` the 26B correction models; `calib_run_info/` the run→source/background mapping |
| `fitter/` | Spectrum fitting: `src/FastGe68Fitter.py` (Ge68, cached MC templates, ~4 s), `src/FastSourceFitter.py` (generic for Cs137/Mn54/Co60/K40, ~0.5 s), `fitters/` (MC templates + classic fallback), `pipeline/run_fit_all.py` (main driver) |
| `run_pipeline.sh` | One-shot sequential driver: `esd2npz` → `fitter`, both outputs under one timestamped directory |
| `output/` | Runtime outputs (not committed), see layout below |

## Physics Background

- **Sources**: Ge68 (positron annihilation, two 511 keV γ), Cs137 (0.662 MeV),
  Mn54 (0.835 MeV), Co60 (1.173 + 1.333 MeV cascade), K40 (1.461 MeV).
  Fits use E_true as the reference.
- **26B energy correction**: applies vertex r-bias correction, 2D spatial
  non-uniformity correction, time-stability correction, and phase absolute
  scale (P1/2 ≈ 0.99340, P3/4 ≈ 0.99743).
- **Selection (background subtraction)**: the calibration run and its mapped
  background run are normalised to event rate (Hz) by LivingTime and
  subtracted; robust criteria are derived from the R_diff curve; the EFV
  ellipse defines the fiducial volume; the energy window is the fitted
  peak μ ± 3σ.
- **Fit model**: Compton MC template (convolved with energy resolution
  σ(E) = √((a/√E)² + b² + (c/E)²)·E) + photopeak Gaussian + C14 pileup;
  outputs μ, σ/E, χ²/ndf.

## Quick Start

```bash
# environment (once per machine)
cd esd2npz && bash setup_env.sh    # create .venv (stages 1-4, pure Python)
cd ../fitter && bash setup_env.sh  # create .venv (fitting)

# one-shot joint run: esd2npz (selection) → fitter (fit)
bash run_pipeline.sh                 # default run 12370 (Ge68)
bash run_pipeline.sh 12370 12295     # explicit calibration runs
```

Output:

```
output/<YYYYmmdd_HHMMSS>/
├── esd2npz/     # results/(npz_raw, npz_corrected, selection_npz, timestamps)
│                # figures/  cuts/ (selection conditions)  logs/  code/ (snapshot)
│                # run_log.{md,json} (with audit)  config_snapshot.json
└── fitter/      # results/(RUN{N}_{source}.npz)  figures/  enl_style_resolution.*
                 # code/  run_log.{md,json}  config_snapshot.json
```

The fitter automatically reads the **same batch's** esd2npz
`results/selection_npz` — no manual hand-off.

Running a single project:

```bash
cd esd2npz && bash run_pipeline.sh 12370 --out-dir <dir>
cd fitter && .venv/bin/python pipeline/run_fit_all.py \
    --input-dir <selection_npz dir> --out-dir <output dir>
```

## Logging & Audit

- **Selection conditions**: `cuts/{RUN}_cuts.json` (ROI, Step-1 energy region,
  z_limit, EFV counts, final energy window) + `cuts/summary.md` multi-run table
- **Code snapshot**: the complete code tree is copied to `code/` per run
  (with `code/sha256.json`) — the exact algorithm version used is
  byte-verifiable
- **End-of-run audit**: verifies the code snapshot is byte-identical to the
  working tree and every deliverable exists; result in
  `run_log.json -> audit`; on failure the script mode exits with **code 3**
  and the agent mode prints a warning
- **Run log**: `run_log.{md,json}` (system / dependencies / config
  fingerprints / per-run event statistics / input-output SHA-256)

## Documentation

- Data processing & provenance: `esd2npz/README.md`, `esd2npz/PROVENANCE.md`
- Fitter design & logging spec: `fitter/README.md`, `fitter/DESIGN_REPORT.md`
- Manuals: `skills/` under both projects (environment / configuration /
  running / troubleshooting / audit)

## Related Documents (Feishu)

- [Processing pipeline & requirements](https://xcnjvifx7evw.feishu.cn/docx/COu3d06GOogbzgxijWccuQJXn2N)
- [Design / implementation report](https://xcnjvifx7evw.feishu.cn/docx/Mxqmdu2BeooCZexGvRncDsgin6g)
