#!/usr/bin/env python3
"""
Stage 4b + Stage 5: external-input contract validation and gamma-peak
aggregation.

Stage 4b — validate the external_inputs/ contract (MANIFEST sha256 match)
Stage 5 — combine per-source peak positions from the fitter results with
pinned historical values (nH/nC/O16, and any missing fitter result) into
the dybmodel input table gamma_AllPhase.dat (fixed 7-peak order), plus an
analysis-style meanEscaleEres table and a provenance sidecar.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import config.paths as P
from src.run_logger import sha256_file

HISTORICAL_KEYS = ["Cs137", "Mn54", "Ge68", "nH", "Co60", "nC", "O16"]


# ---------------------------------------------------------------- stage 4b
def validate_external_inputs() -> dict:
    """Verify every MANIFEST entry's sha256; return a loggable record."""
    manifest_path = Path(P.EXTERNAL_MANIFEST)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"MANIFEST missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    record = {"manifest": str(manifest_path), "files": {}, "all_valid": True}
    for rel, entry in manifest["files"].items():
        path = Path(P.EXTERNAL_INPUTS_DIR) / rel
        info = {"path": str(path), "exists": path.is_file()}
        if info["exists"]:
            actual = sha256_file(path)
            info["sha256"] = actual
            info["sha256_match"] = (actual == entry.get("sha256"))
            if not info["sha256_match"]:
                record["all_valid"] = False
        else:
            info["sha256_match"] = False
            record["all_valid"] = False
        record["files"][rel] = info
    return record


def load_historical_peaks() -> dict[str, tuple[float, float]]:
    """Parse the historical 7-peak table -> {key: (mu, err_rel)}."""
    path = Path(P.EXTERNAL_INPUTS_DIR) / P.HISTORICAL_GAMMA_KEY
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    if len(lines) != 7:
        raise ValueError(f"{path}: expected 7 peaks, got {len(lines)}")
    peaks = {}
    for key, ln in zip(HISTORICAL_KEYS, lines):
        mu, err = ln.split()[:2]
        peaks[key] = (float(mu), float(err))
    return peaks


# ---------------------------------------------------------------- stage 5
def _fitter_peak(key: str, run_id: int, results_dir: Path):
    """Read mu and absolute error from RUN{run_id}_{key}.npz, or None."""
    npz = results_dir / f"RUN{run_id}_{key}.npz"
    if not npz.is_file():
        return None, f"result file not found: {npz}"
    with np.load(npz, allow_pickle=True) as d:
        center = d["center_gauss"].item()
        mu, err = float(center["value"]), float(center["error"])
    if not (mu > 0 and err >= 0):
        return None, f"invalid center_gauss in {npz}: {mu} ± {err}"
    return (mu, err), None


def _amc_peak(key: str, run_id: int, results_dir: Path):
    """AmC 三峰结果。nH/nC: RUN{N}_{nH,nC}.npz 平铺 mu/mu_err（原版
    nH_nC_fitter 输出格式）；O16: RUN{N}_AmC.npz 的 center_gauss_6_13
    （O16Fitter 输出格式；err 可能为 0 —— HESSE 失败/参数贴界，
    下游 MU_ERR_FLOOR 兜底）。"""
    npz_key = "AmC" if key == "O16" else key
    npz = results_dir / f"RUN{run_id}_{npz_key}.npz"
    if not npz.is_file():
        return None, f"result file not found: {npz}"
    with np.load(npz, allow_pickle=True) as d:
        if key == "O16":
            center = d["center_gauss_6_13"].item()
            mu, err = float(center["value"]), float(center["error"])
        else:
            mu, err = float(d["mu"]), float(d["mu_err"])
    if not (mu > 0 and err >= 0):
        return None, f"invalid mu in {npz}: {mu} ± {err}"
    return (mu, err), None


def aggregate_gamma_dat(fitter_results_dir, out_dir, *, phase=None,
                        fold_pre=True, nc_pin=False, runs_override=None
                        ) -> dict:
    """Build the fitter's gamma table (+ sidecars); return per-peak records.

    phase=None  -> AllPhase mode: the fixed reference runs in P.PEAKS;
                   absent results are PINNED to historical values
                   (backward-compatible, byte-identical to before).
    phase=int   -> per-phase mode: the phase's centre runs (selected from
                   CALIB_RUN_TABLE inside the PHASE_TABLE run range),
                   inverse-variance weighted mean of mu per source; absent
                   sources are EXCLUDED (never pinned — a pinned AllPhase
                   number would defeat the purpose of phase separation).
    """
    if phase is not None:
        return _aggregate_phase(fitter_results_dir, out_dir, phase,
                                fold_pre=fold_pre, nc_pin=nc_pin,
                                runs_override=runs_override)
    results_dir = Path(fitter_results_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    historical = load_historical_peaks()

    peaks = []
    warnings = []
    for key, e_true, provider, run_id in P.PEAKS:
        rec = {"key": key, "e_true": e_true, "provider": provider,
               "run_id": run_id, "pinned": provider == "external"}
        if provider in ("fitter", "amc"):
            loader = _fitter_peak if provider == "fitter" else _amc_peak
            got, err_msg = loader(key, run_id, results_dir)
            if got is None:
                warnings.append(f"{key}: {err_msg}; pinned to historical value")
                rec["mu"], rec["err_rel"] = historical[key]
                rec["pinned"] = True
                rec["note"] = err_msg
            else:
                mu, err_abs = got
                err_stat = err_abs / mu if mu > 0 else 0.0
                rec["mu"] = mu
                rec["err_stat_rel"] = err_stat
                rec["err_rel"] = max(err_stat, P.MU_ERR_FLOOR)
                if P.MU_ERR_FLOOR > 0 and err_stat < P.MU_ERR_FLOOR:
                    rec["note"] = (f"err floored {err_stat:.2e} -> "
                                   f"{P.MU_ERR_FLOOR} (stat-only lacks "
                                   f"systematics; historical convention)")
        else:
            rec["mu"], rec["err_rel"] = historical[key]
        # cross-check against the historical table
        hist_mu = historical[key][0]
        rec["mu_historical"] = hist_mu
        rec["dev_vs_historical"] = (rec["mu"] - hist_mu) / hist_mu
        if abs(rec["dev_vs_historical"]) > P.MU_DEVIATION_WARN:
            warnings.append(
                f"{key}: mu deviates from historical by "
                f"{rec['dev_vs_historical']:+.1%} (>{P.MU_DEVIATION_WARN:.0%})")
        peaks.append(rec)

    # ---- gamma_AllPhase.dat (dybGammaData::LoadData order) ----
    dat_path = out_dir / "gamma_AllPhase.dat"
    dat_path.write_text(
        "\n".join(f"{p['mu']:.8f} {p['err_rel']:.8f}" for p in peaks) + "\n")

    # ---- analysis-style table (traceability, gen_gamma_dat.py schema) ----
    tbl = out_dir / "meanEscaleEres_perPhase_CDcenter.dat"
    header = ("Phase,Source,n,mu,err_mu,err_sys_mu,err_stat_mu,"
              "res,err_res,err_sys_res,err_stat_res")
    rows = [f"0,{p['key']},1,{p['mu']:.8f},{p['err_rel']:.8f},0,"
            f"{p['err_rel']:.8f},0,0,0,0" for p in peaks]
    tbl.write_text(header + "\n" + "\n".join(rows) + "\n")

    # ---- provenance sidecar ----
    prov = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "fitter_results_dir": str(results_dir),
        "historical_table": str(
            Path(P.EXTERNAL_INPUTS_DIR) / P.HISTORICAL_GAMMA_KEY),
        "peaks": peaks,
        "warnings": warnings,
        "note": ("e_true follows the dybmodel convention (Ge68 = 1.022 MeV "
                 "annihilation pair, Co60 = 2.506 MeV cascade sum); err_mu is "
                 "RELATIVE. K40 is fitted by the suite but enters dybmodel as "
                 "a spectrum (K40.root), not as one of these 7 peaks."),
    }
    (out_dir / "gamma_AllPhase.dat.provenance.json").write_text(
        json.dumps(prov, indent=2, ensure_ascii=False))

    print(f"[Stage5] wrote {dat_path}")
    for p in peaks:
        flag = " [pinned]" if p["pinned"] else ""
        print(f"  {p['key']:<6} mu={p['mu']:.6f} err={p['err_rel']:.6f}"
              f"  (hist {p['mu_historical']:.6f}, "
              f"dev {p['dev_vs_historical']:+.2%}){flag}")
    for w in warnings:
        print(f"[Stage5][Warning] {w}")
    return {"peaks": peaks, "warnings": warnings,
            "gamma_dat": str(dat_path), "table": str(tbl)}


# ============================================================
# Per-phase aggregation (--phase N)
# ============================================================
def load_phase_ranges():
    """[(phase, run_min, run_max)] from the shared ValProd26B table."""
    import csv
    ranges = []
    with open(P.PHASE_TABLE, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = next(v for v in row.values() if v and v.strip())
            phase = int(name.split()[-1])
            lo, hi = (int(x) for x in row["Run Range"].split("-"))
            ranges.append((phase, lo, hi))
    return sorted(ranges)


def load_calib_runs():
    """[{run, date, x, y, z, source}] from CalibRUN_from_file.csv."""
    import csv
    runs = []
    with open(P.CALIB_RUN_TABLE, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            runs.append({"run": int(r["RUN"]), "date": r["Date"],
                         "x": float(r["X[m]"]), "y": float(r["Y[m]"]),
                         "z": float(r["Z[m]"]), "source": r["Source"]})
    return runs


def select_phase_runs(phase, fold_pre=True):
    """Centre runs per source inside the phase's run range.

    fold_pre (phase 1 only): also take runs BELOW the first range — the
    production tables folded the 2025-08-25 commissioning week into
    Phase 1 (gamma_Phase1_K40.dat has 8 peaks incl. K40 9632), matching
    correction_api.phase_from_run's nearest-phase fallback.
    """
    ranges = load_phase_ranges()
    match = [r for r in ranges if r[0] == phase]
    if not match:
        known = ", ".join(f"P{p} [{lo}-{hi}]" for p, lo, hi in ranges)
        raise ValueError(f"phase {phase} not in {P.PHASE_TABLE} (have {known})")
    _p, lo, hi = match[0]
    first_lo = ranges[0][1]
    sel = {}
    for r in load_calib_runs():
        inside = lo <= r["run"] <= hi
        if not inside and phase == 1 and fold_pre and r["run"] < first_lo:
            inside = True  # pre-P1 commissioning week folded into Phase 1
        if inside and abs(r["z"]) <= P.CENTRE_Z_MAX:
            sel.setdefault(r["source"], []).append(r["run"])
    return {s: sorted(v) for s, v in sel.items()}


def _parse_runs_override(text):
    """'Cs137=12295,Ge68=12370,AmC117=10110,10111' -> {source: [runs]}."""
    out = {}
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            src, runs = part.split("=", 1)
            out[src.strip()] = [int(v) for v in runs.split() if v.isdigit()]
        else:
            out.setdefault("AmC117", []).append(int(part))
    return out


def _weighted_mean(points):
    """points = [(run, mu, err_abs)] -> (mu, err_abs, n_used, n_dropped)."""
    ok = [(rid, m, e) for rid, m, e in points if m > 0]
    if not ok:
        return None
    weights = []
    for _rid, _m, e in ok:
        weights.append(1.0 / (e * e) if e > 0 else 0.0)
    if sum(weights) <= 0:
        mu = float(np.mean([m for _r, m, _e in ok]))
        err = float(np.std([m for _r, m, _e in ok]) / np.sqrt(len(ok))) \
            if len(ok) > 1 else 0.0
    else:
        w = np.asarray(weights)
        m = np.asarray([mm for _r, mm, _e in ok])
        mu = float(np.sum(w * m) / np.sum(w))
        err = float(1.0 / np.sqrt(np.sum(w)))
    return mu, err, len(ok), len(points) - len(ok)


def _aggregate_phase(fitter_results_dir, out_dir, phase, *,
                     fold_pre=True, nc_pin=False, runs_override=None):
    """Per-phase gamma table: weighted mean over the phase's centre runs."""
    results_dir = Path(fitter_results_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    historical = load_historical_peaks()

    sel = select_phase_runs(phase, fold_pre=fold_pre)
    if runs_override:
        for src, runs in _parse_runs_override(runs_override).items():
            sel[src] = runs
        print(f"[Stage5] runs override applied: "
              f"{_parse_runs_override(runs_override)}")

    peaks, warnings = [], []
    for key, e_true, provider, _fixed in P.PEAKS:
        src = "AmC117" if provider == "amc" else key
        runs = sel.get(src, [])
        loader = _fitter_peak if provider == "fitter" else _amc_peak
        points, missing = [], []
        for rid in runs:
            got, err_msg = loader(key, rid, results_dir)
            if got is None:
                missing.append(f"{key}@{rid}: {err_msg}")
            else:
                points.append((rid, *got))
        if not points:
            warnings.append(f"{key}: no usable centre runs in phase {phase} "
                            f"(runs {runs or 'none'} taken) — EXCLUDED")
            for m in missing:
                warnings.append(f"  {m}")
            continue
        mu, err_abs, n_used, n_dropped = _weighted_mean(points)
        if key == "nC" and nc_pin:
            note = (f"nC pinned to production value {P.NC_PIN} "
                    f"(measured {mu:.5f})")
            mu = float(P.NC_PIN)
        else:
            note = None
        err_stat = err_abs / mu if mu > 0 else 0.0
        rec = {"key": key, "e_true": e_true, "provider": provider,
               "phase": phase, "runs": [r for r, _m, _e in points],
               "n_used": n_used, "n_dropped": n_dropped,
               "mu": mu,
               "err_stat_rel": err_stat,
               "err_rel": max(err_stat, P.MU_ERR_FLOOR),
               "pinned": bool(key == "nC" and nc_pin)}
        if note:
            rec["note"] = note
        if missing:
            rec["missing_runs"] = missing
        hist_mu = historical[key][0]
        rec["mu_historical"] = hist_mu
        rec["dev_vs_historical"] = (rec["mu"] - hist_mu) / hist_mu
        if abs(rec["dev_vs_historical"]) > P.MU_DEVIATION_WARN:
            warnings.append(f"{key}: mu deviates from historical by "
                            f"{rec['dev_vs_historical']:+.1%} "
                            f"(>{P.MU_DEVIATION_WARN:.0%})")
        peaks.append(rec)

    if not peaks:
        raise RuntimeError(f"phase {phase}: no peaks with usable runs — "
                           "nothing to aggregate (run peakfit first?)")

    dat_name = f"gamma_Phase{phase}.dat"
    dat_path = out_dir / dat_name
    dat_path.write_text(
        "\n".join(f"{p['mu']:.8f} {p['err_rel']:.8f}" for p in peaks) + "\n")

    tbl = out_dir / "meanEscaleEres_perPhase_CDcenter.dat"
    header = ("Phase,Source,n,mu,err_mu,err_sys_mu,err_stat_mu,"
              "res,err_res,err_sys_res,err_stat_res")
    rows = [f"{phase},{p['key']},{p['n_used']},{p['mu']:.8f},"
            f"{p['err_rel']:.8f},0,{p['err_stat_rel']:.8f},0,0,0,0"
            for p in peaks]
    tbl.write_text(header + "\n" + "\n".join(rows) + "\n")

    prov = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mode": "per-phase",
        "phase": phase,
        "fold_pre_p1_into_p1": fold_pre,
        "nc_pin": nc_pin,
        "fitter_results_dir": str(results_dir),
        "phase_table": str(P.PHASE_TABLE),
        "selection": {s: v for s, v in sel.items()},
        "peaks": peaks,
        "warnings": warnings,
        "excluded": [k for k, _e, _p, _r in P.PEAKS
                     if k not in {p["key"] for p in peaks}],
        "note": ("per-phase caliber: centre runs (|z|<="
                 f"{P.CENTRE_Z_MAX} m), inverse-variance weighted mean; "
                 "absent sources EXCLUDED (not pinned). Production tables "
                 "pinned nC — use --nc-pin to match."),
    }
    (out_dir / f"{dat_name}.provenance.json").write_text(
        json.dumps(prov, indent=2, ensure_ascii=False))

    print(f"[Stage5] wrote {dat_path}  (phase {phase}: "
          f"{len(peaks)}/{len(P.PEAKS)} peaks, excluded: "
          f"{prov['excluded'] or 'none'})")
    for p in peaks:
        pin = " [pinned]" if p["pinned"] else ""
        print(f"  {p['key']:<6} mu={p['mu']:.6f} err={p['err_rel']:.6f}"
              f"  n={p['n_used']} runs={p['runs']}"
              f"  (hist {p['mu_historical']:.6f}, "
              f"dev {p['dev_vs_historical']:+.2%}){pin}")
    for w in warnings:
        print(f"[Stage5][Warning] {w}")
    return {"peaks": peaks, "warnings": warnings,
            "gamma_dat": str(dat_path), "table": str(tbl),
            "phase": phase, "excluded": prov["excluded"]}
