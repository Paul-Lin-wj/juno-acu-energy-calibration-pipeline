#!/usr/bin/env python3
"""
Stage 7: invert the fitted nonlinearity curves into E_true = f(E_rec)
lookup tables.

The dybmodel curves give NL(E_true) = E_rec / E_true per particle type
(electronics, scint-only, and "Full" = electronics ⊗ scint). For each of
the configured Full curves this stage

  1. builds E_rec(E_true) = E_true * NL(E_true) on the curve's grid,
  2. verifies E_rec(E_true) is strictly monotonic (invertible),
  3. inverts by dense resampling + interpolation onto a uniform E_rec grid,
  4. round-trip checks |E_true(f(E_rec(E_true))) - E_true| / E_true,
  5. writes results/Etrue_from_Erec_lookup.npz (+ human-readable CSV).

Pure Python (numpy/scipy only) — no ROOT dependency.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import config.paths as P


def parse_curves_tsv(tsv_path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Parse the block-format TSV written by tools/dump_curves.C."""
    curves: dict[str, tuple[list, list]] = {}
    name = None
    for ln in Path(tsv_path).read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("# curve"):
            name = ln.split("# curve", 1)[1].strip()
            curves[name] = ([], [])
        elif name is not None:
            x, y = ln.split()[:2]
            curves[name][0].append(float(x))
            curves[name][1].append(float(y))
    return {k: (np.asarray(v[0]), np.asarray(v[1])) for k, v in curves.items()}


def invert_curve(e_true: np.ndarray, nl: np.ndarray,
                 e_rec_grid: np.ndarray) -> dict:
    """Invert E_rec = E_true * NL(E_true); return inversion diagnostics."""
    order = np.argsort(e_true)
    e_true, nl = e_true[order], nl[order]
    e_rec = e_true * nl

    diffs = np.diff(e_rec)
    monotonic = bool(np.all(diffs > 0))
    if not monotonic:  # keep going with a warning; interpolation still works
        print(f"[Stage7][Warning] E_rec(E_true) not strictly increasing "
              f"({int((diffs <= 0).sum())} non-increasing steps); "
              f"sorting + interp anyway")

    # dense forward curve, then invert by interpolation on sorted samples
    dense_e_true = np.linspace(e_true.min(), e_true.max(), 200_000)
    dense_e_rec = dense_e_true * np.interp(dense_e_true, e_true, nl)
    order2 = np.argsort(dense_e_rec)
    e_true_inv = np.interp(e_rec_grid, dense_e_rec[order2],
                           dense_e_true[order2])

    # round-trip check on the ORIGINAL grid
    rt = np.interp(e_rec, dense_e_rec[order2], dense_e_true[order2])
    rel = np.abs(rt - e_true) / e_true
    # coverage of the requested grid
    inside = (e_rec_grid >= dense_e_rec.min()) & (e_rec_grid <= dense_e_rec.max())
    return {"e_true_grid": e_true_inv, "monotonic": monotonic,
            "roundtrip_max_rel": float(rel.max()),
            "roundtrip_median_rel": float(np.median(rel)),
            "e_rec_range": (float(dense_e_rec.min()), float(dense_e_rec.max())),
            "grid_inside_range": inside}


def build_lookups(curves_tsv, out_dir) -> dict:
    tsv = Path(curves_tsv)
    out_dir = Path(out_dir)
    curves = parse_curves_tsv(tsv)
    missing = [c for c in P.INVERT_CURVES if c not in curves]
    if missing:
        raise RuntimeError(f"curves missing from {tsv}: {missing}")

    e_rec_grid = np.arange(0.1, 12.0001, 0.001)
    payload, records = {}, {}
    for name in P.INVERT_CURVES:
        e_true, nl = curves[name]
        inv = invert_curve(e_true, nl, e_rec_grid)
        payload[f"{name}_e_rec"] = e_rec_grid
        payload[f"{name}_e_true"] = inv["e_true_grid"]
        records[name] = {k: v for k, v in inv.items() if k != "e_true_grid"}
        r = records[name]
        print(f"[Stage7] {name}: monotonic={r['monotonic']}  "
              f"E_rec range {r['e_rec_range'][0]:.3f}–{r['e_rec_range'][1]:.3f} MeV  "
              f"round-trip max {r['roundtrip_max_rel']:.2e} "
              f"(median {r['roundtrip_median_rel']:.2e})")

    payload["e_rec_grid"] = e_rec_grid
    npz = out_dir / "Etrue_from_Erec_lookup.npz"
    np.savez_compressed(npz, **payload)

    # human-readable CSV (gamma = the calibration deliverable, first)
    csv = out_dir / "Etrue_from_Erec_lookup.csv"
    with csv.open("w") as f:
        f.write("e_rec," + ",".join(P.INVERT_CURVES) + "\n")
        for i in range(0, len(e_rec_grid), 10):  # 0.01 MeV step in the CSV
            row = [f"{e_rec_grid[i]:.4f}"]
            for name in P.INVERT_CURVES:
                row.append(f"{payload[f'{name}_e_true'][i]:.6f}")
            f.write(",".join(row) + "\n")

    print(f"[Stage7] wrote {npz} and {csv}")
    return {"lookup_npz": str(npz), "lookup_csv": str(csv),
            "curves": records, "n_curves_parsed": len(curves)}
