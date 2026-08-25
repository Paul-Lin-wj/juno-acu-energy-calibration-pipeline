# Skill: Physics QA Figures — human-judgeable checks without reference data

## Description

How to read the per-run physics QA page (`figures/physics_qa/Run{R}_physics_qa.png`)
and its JSON twin. Use this skill for production sign-off: one glance per run
should catch most data/chain problems.

---

## Generating

Automatic as Stage 4 of every pipeline run. Manually:

```bash
.venv/bin/python tools/make_physics_qa.py --run 12370 \
    --corrected-dir output/<ts>/results/npz_corrected \
    --selection-npz output/<ts>/results/selection_npz/Run12370_SelectionResult.npz \
    --out-dir output/<ts>/figures/physics_qa
```

## The 8 Panels and What "Bad" Looks Like

| Panel | Content | Failure signature |
|---|---|---|
| **A** full spectrum (log-y) | source γ lines (red), Compton edges (dotted), K40/Tl208 lines (gray dashed); veto % and E<0 junk % in the title | peak far from its marker; distorted continuum; junk % ≫ few % |
| **B** EFV spectrum + fit | fitted μ and σ/E annotated | no/many peaks; σ/E wildly off (~3–4 % at 1 MeV is normal) |
| **C** ρ–Z vertex density | red cloud = EFV-selected; ★ = source position; title shows centroid distance | cloud not centred on ★; EFV cloud clipped wrongly |
| **D** X–Y vertex density | ★ = source | off-centre or lopsided reconstruction |
| **E** energy vs time | median E per time bin ± MAD, max drift % in title | slope/steps → detector drift or correction failure |
| **F** rate vs time | Hz per bin; mean, rms/mean | gaps → DAQ holes; jumps → source/DAQ state change |
| **G** totalPE vs E | 2D density + median profile; adjacent-bin jump % | steps/kinks in profile → PE or energy branch inconsistency |
| **H** numeric summary | all quantities above as text | use as the checklist |

## JSON Twin — `Run{R}_physics_qa.json`

Same numbers, machine-readable, ideal for batch screening across many runs:
flag runs with e.g. `vertex_centroid_dist_mm > 100`, `energy_drift_pct > 5`,
`rate rms/mean > 10 %`, fitted peak missing (`fitted_peaks == []`).

## Baseline Values (RUN 12370, Ge68 @ center, 2025-12-17)

- fitted peak 0.9094 MeV, σ/E 3.56 %
- vertex centroid distance 0.3 mm
- rate 392.5 ± 3.4 Hz (rms/mean 0.9 %), energy drift 2.6 %
- veto 5.3 %, E<0 junk 2.6 % (calibration runs)
- physics (background) runs look very different: junk fraction can be ~80 %
  (failed reconstructions dominate) — that is expected, not a failure

## Cross-Check with the Fitter

The fitter's own μ (0.9102 MeV) and σ/E (3.54 %) for the same run should
agree with panel B within fit-model differences — a large disagreement means
the selection NPZ handed over is not the one you QA'd.
