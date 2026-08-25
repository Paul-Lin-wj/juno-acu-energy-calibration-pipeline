# Skill: Audit & Verification — bitwise comparison against the original chain

## Description

How to prove the standalone chain reproduces the original production chain
**bitwise**, and how to re-audit after any change. This is the fallback /
acceptance tool: production physics QA uses skill 08 instead.

---

## The Audit Tool

`tools/make_audit_report.py` compares this pipeline's outputs against
reference files from the original chain and writes overlay spectra, residual
panels, an EDM per-branch difference plot and a field-by-field table.

```bash
# reference files (copy once from lustrefs; see PROVENANCE.md)
mkdir -p data/_audit_ref && cd data/_audit_ref
REF=/lustrefs/juno26/users/zhaorz/Calib/ReProd26B
cp $REF/npz_from_root/esd/RUN12370.npz                     REF_raw_RUN12370.npz
cp $REF/Finalcorrection_from_npzESD/Data/RUN12370.npz      REF_corr_RUN12370.npz
cp $REF/singles_selection/Results_fromFinalcorrection/npz/Run12370_SelectionResult.npz \
   REF_sel_RUN12370.npz
cd ../..

.venv/bin/python tools/make_audit_report.py     # → audit_report/
```

Expected result for an unmodified chain: every field `bitwise_equal=True`,
`maxdiff=0`, residual panels flat at 0, EDM branches all "0 (bitwise)" except
the known `totalPE` (orange, ~2e-4, unused downstream).

## What Was Verified on 2026-08-24 (acceptance record)

| Comparison | Result |
|---|---|
| Stage-1 NPZ vs `npz_from_root/esd/RUN12370.npz` (1.49 M events × 10 fields) | **bitwise identical** |
| Stage-2 NPZ vs `Finalcorrection.../Data/RUN12370.npz` | **bitwise identical** |
| Stage-3 selection NPZ vs `Results_fromFinalcorrection/npz/...` (109 212 × 5) | **bitwise identical** |
| Background run 12419 raw + corrected | **bitwise identical** |
| Timestamps (wo_Ecut / Ecut) vs previous run | identical |
| locally rebuilt EDM (`--full-esd`) vs reference chunks | all branches bitwise identical **except** `totalPE` (median 2.1e-4, 97 % < 0.3 %) — May vs June JUNOSW build |
| pure-copy inputs (correction api/data, run tables, libpcre) | md5 identical to originals |
| `src/` port vs original sources | statement-level identical algorithms (PROVENANCE.md §2) |

Downstream cross-check: `standalone_fitter` fed with the standalone selection
NPZ reproduces its historical fit results field-for-field
(mu=0.9102 MeV, σ/E=3.54 %, all 23 result fields identical).

## When to Re-Audit

- after **any** change to `src/`, `input/correction/`, or `calib_run_info/`
- after a python/numpy/uproot major-version jump
- after moving `REMOTE_EDM_DIR` to a different dataset build

Minimal re-audit: rerun run 12370 in from-edm mode, regenerate the audit
report, confirm all fields still bitwise-equal, and record the result in
`PROVENANCE.md`.

## Built-in per-run audit (automatic)

Every pipeline run already ends with an **automatic completeness audit** —
no manual step needed:

- `output/<ts>/code/` holds a **full copy of the code tree** used for that
  run, with `code/sha256.json` fingerprints;
- the audit verifies (a) every code file exists in `code/` and is
  byte-identical to the working tree (missing/mismatched/extra detection)
  and (b) every deliverable file is present;
- result in `run_log.json -> audit` / `run_log.md -> Audit`;
- on failure: script mode exits with **code 3** (no `latest` publish),
  agent mode prints `[AUDIT] WARNING` and marks status `audit-failed`.

So a third party can verify a run's provenance by: `run_log.json` → git
commit → `code/` (byte-identical snapshot) → input/output SHA-256 → cuts
values → stage logs. See skill 07 for details.

## Code Freeze Checksums

Compare live files against the audited md5s (skill 05 lists them); any
mismatch invalidates the bitwise guarantee until re-audited.
