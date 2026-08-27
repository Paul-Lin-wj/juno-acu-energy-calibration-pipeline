# JUNO ACU Energy Nonlinearity Calibration Pipeline

[中文版](README.md)

## Overview

Processing pipeline for JUNO (Jiangmen Underground Neutrino Observatory)
ACU (Automatic Calibration Unit) gamma-source calibration data.
The complete physics chain for the energy-nonlinearity / resolution
measurement is:

> waveform reconstruction → event reconstruction → event selection
> (calibration sources & continuous-spectrum nuclides) → peak fitting /
> continuous-spectrum fitting → nonlinearity curve fitting →
> E_true = f(E_rec)

This repository now covers the **EDM → E_true=f(E_rec)** main chain
(26B energy correction, event selection, physics QA, peak fitting, and
the global nonlinearity fit), covering five single-line calibration
sources — Ge68 / Cs137 / Mn54 / Co60 / K40 — plus the **AmC
correlated-pair chain** (n-H / n-12C / O16 peaks, the `calibsel` AmC branch). The
continuous-spectrum preparation is still being absorbed — see the
coverage table and integration plan below.

```text
Complete physics chain and coverage
(✅ present in this repo | 🔶 code exists, to be absorbed | ⚠️ external dep, optional | ❌ missing, use existing data for now)

❌ Waveform reconstruction (PMT waveform → charge/time)     [upstream JUNOSW; plan: wrap as an
   │                                                         optional stage, env fingerprint
   │                                                         recorded in run_log]
   ▼
⚠️ Event reconstruction (OMILREC energy/vertex)             [optional Stage 0 --full-esd calls the
   │                                                         external CVMFS/JUNOSW; plan: switch to
   │                                                         the standalone omilrec (tag-pinned
   │                                                         algorithm version); the default
   │                                                         from-edm mode reads the pre-existing
   │                                                         ReProd26B EDM chunks on lustrefs]
   ▼  calibsel/
✅ Stage 1   EDM → NPZ (per-run merged events + LivingTime)
   ▼
✅ Stage 2   26B Finalcorrection (r-bias vertex + spatial + time + phase
   │         absolute scale; mapped background run processed automatically)
   ▼
✅ Stage 3   Calibration-source event selection (MuonVeto → robust ROI →
   │         Z-cut → EFV ellipse → energy window; calibration and background
   │         runs normalised to event rate by LivingTime and subtracted)
✅ Stage 3c  AmC correlated-pair selection (prompt–delayed time window +
   │         distance correlation → nH/nC/O16 events)       [calibsel AmC branch: correlate_selection
   │                                                         absorbed verbatim (only 2 import
   │                                                         lines localised); output matches
   │                                                         production value-for-value]
❌            Continuous-spectrum nuclide selection          [preparation code not yet obtained;
   │                                                         use existing data as declared
   │                                                         external inputs (contract + manifest)]
   ▼
   Run{N}_SelectionResult.npz / correlation_result_RUN{N}.npz (fitter input)
   ▼  peakfit/
✅ Calibration-source peak fitting (MC template convolution + Minuit
   │         → μ / σ/E / χ²) + ENL-style resolution summary plot
   │         (reference curve uses fixed parameters, not fitted)
✅ n-H / n-12C / O16 peak fitting                            [fitter run_amc_fit_all: nH/nC pure
   │                                                         Gaussian (NhnCFitter, verbatim
   │                                                         port) + O16 template decomposition
   │                                                         (O16Fitter)]
❌ Continuous-spectrum fitting                                [dybmodel already embeds the
   │                                                         B12/C10/C11/Michel fit machinery;
   │                                                         inputs use existing data for now]
   ▼  nlfit/ (new module, wired in)
✅ Stage 4b  External-data contract validation (continuous spectra + interim
   │         nH/nC/O16 historical values, MANIFEST sha256)
   ▼
✅ Stage 5   Aggregate per-source μ/σ → meanEscaleEres table → gamma_AllPhase.dat
   │                                                         [pure Python; missing
   │                                                         peakfit sources auto-pinned
   │                                                         to historical + warning]
   ▼
✅ Stage 6   Global nonlinearity fit (dyb model, E_rec/E_true vs E_true)
   │                                                         [wrap ENL_agent/
   │                                                         fitter_energynl_dybmodel (C++);
   │                                                         sandbox + 2 documented
   │                                                         non-physics patches,
   │                                                         cvmfs J26.1.1, probed]
   ▼
✅ Stage 7   E_rec → E_true inversion → E_true = f(E_rec) lookup table
                                                             [pure Python (e⁻/e⁺/γ curves,
                                                             round-trip ≤2e-5)]
```

### Coverage at a glance

| Physics-chain stage | Status | Location / notes |
| --- | :---: | --- |
| Waveform reconstruction | ❌ | Upstream JUNOSW product; plan: wrap as an optional stage |
| Event reconstruction | ⚠️ | Optional Stage 0 in `calibsel` (`--full-esd`, external JUNOSW, hours); plan: switch to the standalone omilrec; default starts from the pre-existing EDM on lustrefs |
| Calibration-source event selection | ✅ | `calibsel` Stages 1–3 + Stage 4 physics QA (8-panel figure + JSON) |
| AmC correlated-pair selection (n-H/n-12C/O16) | ✅ | `calibsel` AmC branch (correlate_selection absorbed verbatim, output matches production value-for-value; centre-run triple peak vs AllPhase within 1.2%) |
| Continuous-spectrum nuclide selection | ❌ | Preparation code not yet obtained; use existing data as declared external inputs (MANIFEST contract) |
| Calibration-source peak fitting | ✅ | `peakfit` (fast: Ge68 ~4 s, others ~0.5 s; classic fallback) |
| n-H/n-12C/O16 peak fitting | ✅ | `peakfit/pipeline/run_amc_fit_all`: nH/nC pure Gaussian (`NhnCFitter` verbatim port) + O16 template decomposition (`O16Fitter`; minuit HESSE state recorded in run_log) |
| Continuous-spectrum fitting | ❌ | dybmodel embeds the fit machinery; upstream inputs use existing data for now |
| Nonlinearity curve fit | ✅ | `nlfit` Stage 6: wraps `ENL_agent/fitter_energynl_dybmodel` (sandbox + behaviour lock) |
| E_true=f(E_rec) inversion | ✅ | `nlfit` Stage 7: pure Python, e⁻/e⁺/γ lookup curves |

### Integration plan

| Priority | Stage | Content | Source | Approach | Status |
| --- | --- | --- | --- | --- | --- |
| ★★★ | 4b | External-data contract (continuous spectra + interim nH/nC/O16 values) | dybmodel `necessaryfiles/` etc. | validate + MANIFEST (SHA-256) | ✅ landed (`nlfit`) |
| ★★★ | 5 | Aggregate per-source μ/σ → `gamma_AllPhase.dat` | ENL_agent `glue/gen_gamma_dat.py` | port (pure Python) | ✅ landed (`nlfit`) |
| ★★★ | 6 | Global nonlinearity fit | `fitter_energynl_dybmodel` | wrap (C++, cvmfs J26.1.1; probed) | ✅ landed (`nlfit`) |
| ★★☆ | 7 | E_rec→E_true inversion to a lookup table | new code | pure Python (monotonicity + round-trip check) | ✅ landed (`nlfit`) |
| ★☆☆ | 3c/3b | AmC correlated-pair selection + nH/nC/O16 peak fitting | `correlate_selection` + `AmC_nH-nC_fitter` / this repo's `O16Fitter` | `calibsel` AmC branch (verbatim absorption) + `peakfit` `run_amc_fit_all`; nlfit PEAKS triple provider=`amc` | ✅ landed |
| ☆☆☆ | 0/-1 | Full waveform/event reconstruction chain | JUNOSW / standalone omilrec | optional mode + `data_lineage` record (not bitwise-identical to ReProd26B, must stay traceable) | ⬜ pending |

New stages reuse the existing chassis (RunLogger / code snapshot / audit /
exit codes / `--launched-by agent`); the top-level `run_pipeline.sh` now runs
calibsel → peakfit → nlfit. The sibling workspace
`/datafs/users/wujxy/agent-sci/ENL_agent/` (DSH orchestration, `.dsh/skills/`)
remains the code source for the 🔶 modules, and dybmodel itself is consumed
read-only by `nlfit` (auto-rebuilt sandbox, inputs/outputs sha256-recorded).

Every step's selection conditions (ROI, z_limit, energy window, ...) are
archived with the run; each run also ships a **complete code snapshot** and an
**end-of-run completeness audit**, so results are fully traceable.

## Repository Layout

| Path | Purpose |
|---|---|
| `calibsel/` | Data-processing pipeline: EDM→NPZ→26B correction→selection. `src/` is the algorithm code (line-by-line port of the original production chain; outputs bitwise identical to it); `pipeline/` holds orchestration & audit logging; `input/correction/` the 26B correction models; `calib_run_info/` the run→source/background mapping  The AmC branch lives in `src/amc/` (driver `pipeline/run_amcsel_all.py`, provenance in `PROVENANCE.amc.md`). |
| `peakfit/` | Spectrum fitting: `src/FastGe68Fitter.py` (Ge68, cached MC templates, ~4 s), `src/FastSourceFitter.py` (generic for Cs137/Mn54/Co60/K40, ~0.5 s), `fitters/` (MC templates + classic fallback), `pipeline/run_fit_all.py` (main driver), `pipeline/run_amc_fit_all.py` (AmC triple peak: nH/nC pure Gaussian `NhnCFitter` + O16 template decomposition) |
| `nlfit/` | Global nonlinearity fit (Stages 4b/5/6/7): external-data contract, 7-peak aggregation to `gamma_AllPhase.dat`, dybmodel C++ wrap (auto-rebuilt sandbox + behaviour lock), E_rec→E_true inversion lookup; `external_inputs/` holds the interim external-data contract |
| `run_pipeline.sh` | One-shot sequential driver: `calibsel` (gamma + AmC selection) → `peakfit` → `nlfit`, all outputs under one timestamped directory |
| `output/` | Runtime outputs (not committed), see layout below |

## Physics Background

- **Sources**: Ge68 (positron annihilation, two 511 keV γ), Cs137 (0.662 MeV),
  Mn54 (0.835 MeV), Co60 (1.173 + 1.333 MeV cascade), K40 (1.461 MeV).
  Fits use E_true as the reference.
- **AmC neutron source** (²⁴¹Am–¹³C): ¹³C(α,n)¹⁶O* yields the O16 6.129 MeV
  line (prompt) plus the thermalised-neutron capture peaks n-H 2.2233 MeV
  and n-12C 4.945 MeV (delayed); after prompt–delayed correlated-pair
  selection (`calibsel` AmC branch, capture time τ≈211 μs) they are fitted by `peakfit`
  and supply 3 of the 7 gamma peaks entering the nonlinearity fit. Note the
  ACU AmC source scans along z (±17.3 m): compare against the AllPhase
  historical values with **centre runs** (edge runs show %-level position
  offsets — a real effect, not a bug).
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
cd calibsel && bash setup_env.sh    # create .venv (stages 1-4, pure Python)
cd ../peakfit && bash setup_env.sh # create .venv (fitting)
cd ../nlfit  && bash setup_env.sh  # create .venv (aggregate/invert; Stage 6 needs
                                   #   the self-built container or cvmfs ROOT)

# one-shot joint run: calibsel (gamma singles + AmC correlated pairs)
#                      → peakfit (fit) → nlfit (NL fit + inversion)
bash run_pipeline.sh                 # default gamma 12370 (Ge68) + AmC 10110
bash run_pipeline.sh 12370 10110     # explicit runs (auto-routed per source type)
NLFIT_FLAGS="--skip-dybmodel" bash run_pipeline.sh   # skip Stage 6/7 without container
# AmC inputs (RUN10110 + bkg 10100) are pre-staged in calibsel/input/amc_data/;
# for other runs fetch the Finalcorrection npz per calibsel/PROVENANCE.amc.md §3
```

Output:

```text
output/<YYYYmmdd_HHMMSS>/
├── calibsel/     # results/(npz_raw, npz_corrected, selection_npz, timestamps)
│                # figures/  cuts/ (selection conditions)  logs/  code/ (snapshot)
│                # run_log.{md,json} (with audit)  config_snapshot.json
├── calibsel_amc/ # AmC branch: results/RUN{N}/correlation_result_RUN{N}.npz
├── peakfit/     # results/(RUN{N}_{source}.npz, RUN{N}_{nH,nC,AmC}.npz)
│                # figures/  enl_style_resolution.*  code/  run_log.{md,json}
│                # config_snapshot.json
├── peakfit_amc/ # AmC triple-peak fit archived separately (npz merged into peakfit/results)
└── nlfit/       # results/(gamma_AllPhase.dat, bestFit_*.dat, nl_curves.tsv,
                 #          Etrue_from_Erec_lookup.npz/csv)
                 # figures/(stage5_gamma_peaks, stage6_nl_curves,
                 #          stage7_inversion, dybmodel/)
                 # code/  run_log.{md,json}  config_snapshot.json
```

peakfit automatically reads the **same batch's** calibsel
`results/selection_npz`, and nlfit the same batch's peakfit `results/` —
no manual hand-off anywhere in the chain.

Running a single project:

```bash
cd calibsel && bash run_pipeline.sh 12370 --out-dir <dir>
cd peakfit && .venv/bin/python pipeline/run_fit_all.py \
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

- Data processing & provenance: `calibsel/README.md`, `calibsel/PROVENANCE.md`
- AmC branch selection & provenance: `calibsel/README.amc.md`, `calibsel/PROVENANCE.amc.md`
- Fitter design & logging spec: `peakfit/README.md`, `peakfit/DESIGN_REPORT.md`
- Nonlinearity fit & external-data contract: `nlfit/README.md`, `nlfit/external_inputs/MANIFEST.json`
- Manuals: `skills/` under each module (environment / configuration /
  running / troubleshooting / audit)

## Related Documents (Feishu)

- [MiniESD2npz pipeline report](https://xcnjvifx7evw.feishu.cn/docx/COu3d06GOogbzgxijWccuQJXn2N)
- [Calibration peak fitting](https://xcnjvifx7evw.feishu.cn/docx/Mxqmdu2BeooCZexGvRncDsgin6g)
