# Skill: Pipeline Internals — stages, data flow, and the algorithm freeze

## Description

How the four stages work internally, what data crosses each boundary, and the
rules that keep the physics code frozen. Use this skill before changing any
orchestration logic or adding a stage.

---

## Data Flow & File Formats

### Stage 1 — EDM → NPZ (`src/convert_edm_to_npz.py`)

- Input: EDM ROOT chunks `run_{R}_{i}_{j}.root` (trees `CDCalib` + `Time`)
- Branches read: `global_time_s, global_time_ns, trigger_type, MuonVeto,
  totalPE, omilrec_x/y/z, omilrec_energy`
- Chunks are sorted by numeric range `(start, end)` before merging
- LivingTime: `Σ TLTime_s + Σ TLTime_ns/1e9` over the `Time` tree
  (old-style single `TLTime` [ns] also supported)
- Output: `RUN{R}.npz` with the 9 arrays + scalar `LivingTime`

### Stage 2 — 26B Finalcorrection (`src/apply_final_correction.py`)

Exact call sequence on `EnergyCorrection26B` (the physics; never reorder):

```
x_corr, y_corr, z_corr = corr.correct_vertex_rbias(x, y, z, "mm")
spatial  = corr.spatial_factor_from_position(x_corr, y_corr, z_corr, run=R, "mm")
time_f   = corr.time_factor(event_time)             # event_time = s + ns/1e9
phase    = corr.phase_from_run(R)
abs_scale= corr.absolute_scale_for_phase(phase)     # P1/2 0.99340419, P3/4 0.99743135
total    = spatial * abs_scale / time_f
energy_corr = float64(energy) * total  →  cast back to float32
```

Vertex arrays are replaced by the r-bias-corrected ones; all other keys pass
through unchanged.

### Stage 2b — background run

`calib_to_analyze.txt` maps e.g. `Ge68,12344-12409,12419` → background run
12419. The orchestrator runs stages 1–2 for it whenever its corrected NPZ is
missing. Selection needs it for bkg subtraction counts.

### Stage 3 — Selection (`src/combine_selection.py`, 976 lines)

Sequence: load NPZs → MuonVeto keep → robust ROI scan
(`fit_quadratic_plus_gaussian_grid` over mu±nσ grid) → Step-1 energy region →
Z-cut robust crossing (RD threshold 0.08 %, 5-point check) → EFV ellipse →
energy-window fit (mu±3σ) → outputs. See skill 07 for the cut details.

### Stage 4 — physics QA (`tools/make_physics_qa.py`)

Reads the corrected NPZ + selection NPZ only; no influence on results.

## The Algorithm Freeze Rules

1. **Never edit `src/*.py` or `input/correction/*` for convenience.** These
   files are the audited port (PROVENANCE.md) whose output was verified
   bitwise against the original production chain.
2. The orchestrator (`pipeline/run_all.py`) may only **call** the stage
   scripts with different arguments (paths, runs, slices) — never reimplement
   or wrap their logic.
3. Every run archives `code_snapshot/` with sha256 of all algorithm files.
   If a checksum changes, the run log says so implicitly — compare against
   the audited values:

   ```
   src/apply_final_correction.py   889228fd86b34fb47a3dd40723eb7c4e
   src/combine_selection.py        f7c8d19806565f16e3128d6ecfc8f2a2
   src/convert_edm_to_npz.py       8e6a72599610fac19aeb449c79bcf107
   src/esd_to_edm.py               c55ffe777905a088bc6f8465845e7f94
   src/list_esd.py                 5cedec88703499ed6187a34e921f1df6
   src/local_utils.py              46265f86064c339427cc0c678233781d
   input/correction/correction_api.py 8ce74ba51618feee85f12a24e33d7f17
   ```

   (also in `code_snapshot/sha256.json` of any pre-change run).
4. If a change to the physics is genuinely required, it must go through a new
   audit (skill 10) and a PROVENANCE.md entry — never silently.

## Known Intentional Non-Identical Branch

`totalPE` from locally rebuilt EDM (`--full-esd`, June JUNOSW build) differs
microscopically from the May reference (median 2e-4 relative, 97 % < 0.3 %).
Everything downstream of stage 1 does not read `totalPE`; the selection NPZ
contains only `calib_index` + `calib_omilrec_*`. Stage 1 output is bitwise
identical for all other branches.
