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


def aggregate_gamma_dat(fitter_results_dir, out_dir) -> dict:
    """Build gamma_AllPhase.dat (+ sidecars); return per-peak records."""
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
