# Skill: Project Overview — standalone_esd2npz

## Description

This skill provides a comprehensive overview of the **standalone_esd2npz**
project — the JUNO ReProd26B calibration data reduction pipeline that turns
EDM/ESD raw reconstruction output into the selection NPZ consumed by
`standalone_fitter`. Use this skill when you need to understand what the
project does, its architecture, and when to apply it.

---

## What This Project Does

It is the self-contained port of the **ESD→EDM→NPZ→26B-correction→selection**
segment of `juno_calibration_acu_gamma_source`. For each calibration run it
produces:

1. **Raw NPZ** (`results/npz_raw/RUN{R}.npz`) — merged per-run events from EDM
   chunks (CDCalib tree) + LivingTime from the Time tree
2. **Corrected NPZ** (`results/npz_corrected/RUN{R}.npz`) — 26B energy
   correction applied (r-bias vertex, 2D spatial, v2 time, phase absolute scale)
3. **Selection NPZ** (`results/selection_npz/Run{R}_SelectionResult.npz`) —
   the fitter input: `calib_index`, `calib_omilrec_energy/x/y/z` after
   MuonVeto + robust energy ROI + Z-cut + EFV ellipse selection
4. **Physics QA page** (`figures/physics_qa/Run{R}_physics_qa.png`) —
   human-readable intrinsic physics checks (no reference data needed)
5. **Cut archive** (`cuts/{R}_cuts.json` + `cuts/summary.md`) — every
   selection condition decided for this run (see skill 07)

### Pipeline Stages

```
              (optional, --full-esd)
EOS ESD ──► Stage 0  esd_to_edm.py     MySimpleTag reconstruction (CVMFS+JUNOSW)
   ────────────────────────────────────────────────────────────────────────
lustrefs EDM ─► Stage 1  convert_edm_to_npz.py      per-run NPZ + LivingTime
             ─► Stage 2  apply_final_correction.py  26B correction
             ─► Stage 2b (auto) same for the background physics run
             ─► Stage 3  combine_selection.py        cuts → SelectionResult.npz
             ─► Stage 4  make_physics_qa.py          physics QA figures
```

### Default Mode ("from-edm")

**The pipeline starts from the pre-existing ReProd26B EDM chunks on lustrefs**
(`config/paths.py: REMOTE_EDM_DIR`, 2799 chunks). This is the old
`--skip-esd` behaviour, now the default — no CVMFS, no JUNOSW, no EOS access
is required. `--full-esd` opts into local ESD→EDM reconstruction.

### Supported Sources

All sources mapped in `calib_run_info/calib_to_analyze.txt`
(Ge68 / Cs137 / Mn54 / Co60 / K40 / AmC…). The selection code carries the
nominal energies for Cs137 0.662, Mn54 0.835, Ge68 1.022, K40 1.461,
Co60 2.506, nH/AmC 2.223, nC 4.94, O16 6.13 MeV.

### Key Design Decisions

- **Algorithm freeze**: every file under `src/` is the audited, byte-verified
  port of the original chain (see `PROVENANCE.md`). The pipeline orchestrator
  NEVER edits them; it only calls them with explicit arguments.
- **Audit trail by default**: each run gets `output/<timestamp>/` with
  run_log.{md,json}, config_snapshot.json, console.log, per-stage logs,
  code_snapshot/ (sha256 of the algorithm files) and cuts/.
- **Numeric guarantee**: with the same EDM inputs the chain reproduces the
  original production NPZs **bitwise** (verified 2026-08-24; see skill 10).
- **Pure Python** for stages 1–4 (numpy/pandas/scipy/matplotlib/uproot).
