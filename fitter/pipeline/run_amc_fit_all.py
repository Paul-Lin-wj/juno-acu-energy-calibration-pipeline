#!/usr/bin/env python3
"""
run_amc_fit_all.py — AmC 关联对三峰拟合入口（Stage 3b 的 AmC 部分）。

输入：amcsel 的挑选结果 correlation_result_RUN{N}.npz
      （键：prompt_energy / delay_energy / nH_energy，omilrec 能量）
输出（与 gamma 源同一约定 RUN{N}_{src}.npz，供 nlfit Stage5 统一消费）：
      results/RUN{N}_nH.npz   nH  2.22 MeV 纯高斯（NhnCFitter，原版移植）
      results/RUN{N}_nC.npz   nC  4.95 MeV 纯高斯（NhnCFitter，原版移植）
      results/RUN{N}_AmC.npz  O16 6.13 MeV 模板分解（O16Fitter，经
                               MCBased_Fitter.build_fitter 原样调用，
                               μ 即 center_gauss_6_13）

nH/nC 拟合窗口与初值 = NhnCFitter.FIT_CONFIG 原值；O16 bins/参数 =
build_fitter('AmC') 原值。本文件只做编排，不改任何拟合数字。

Usage:
    .venv/bin/python pipeline/run_amc_fit_all.py --run 10104 \
        --corr-npz <amcsel>/results/RUN10104/correlation_result_RUN10104.npz \
        [--out-dir <dir>] [--peaks nH,nC,AmC]
"""
from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time
from pathlib import Path

_PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ_ROOT))
for _p in ["src", "fitters", "smx_ana", "pipeline"]:
    _path = str(_PROJ_ROOT / _p)
    if _path not in sys.path:
        sys.path.insert(0, _path)
os.environ.setdefault("MPLCONFIGDIR", str(_PROJ_ROOT / "TMP" / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config.paths import PROJECT_ROOT
from src.run_logger import RunLogger
from src.NhnCFitter import GaussianFitter, FIT_CONFIG, MIN_EVENTS

# 与 nlfit config/paths.py 的 PEAKS 同源（E_true，MeV）
E_TRUE = {"nH": 2.2233, "nC": 4.95, "AmC": 6.129}


def load_amc_energies(corr_npz: Path) -> dict:
    """从关联挑选结果取三段能量（键名即 amcsel 输出约定，未做变换）。"""
    with np.load(corr_npz, allow_pickle=True) as d:
        keys = set(d.files)
        out = {}
        if "nH_energy" in keys:
            out["nH"] = d["nH_energy"].astype(np.float64)
        if "delay_energy" in keys:
            de = d["delay_energy"].astype(np.float64)
            pmin, pmax = FIT_CONFIG["nC"]["plot_range"]
            out["nC"] = de[(de >= pmin) & (de <= pmax)]
        if "prompt_energy" in keys:
            out["AmC"] = d["prompt_energy"].astype(np.float64)
        return out


def fit_gaussian_peak(peak: str, energy: np.ndarray, run_id: int,
                      res_dir: Path, fig_dir: Path) -> dict | None:
    """nH/nC 纯高斯拟合 —— 与原版 nH_nC_fitter.fit_run 逐步一致。"""
    cfg = FIT_CONFIG[peak]
    fmin, fmax = cfg["fit_range"]
    n_fit = int(np.sum((energy >= fmin) & (energy <= fmax)))
    if n_fit < MIN_EVENTS[peak]:
        print(f"[skip] RUN{run_id} {peak}: {n_fit} events in fit range "
              f"(< {MIN_EVENTS[peak]})")
        return None
    print(f"RUN{run_id} {peak}: {len(energy)} events in plot window, "
          f"{n_fit} in fit range -- fitting ...", end="", flush=True)
    ftr = GaussianFitter(
        energy,
        plot_range=cfg["plot_range"],
        fit_range=cfg["fit_range"],
        init_mu=cfg["init_mu"],
        init_sigma=cfg["init_sigma"],
        bins=100,
    )
    valid = ftr.fit()
    r = ftr.result
    print(f" mu={r['mu']:.4f} MeV, sigma={r['sigma']:.4f} MeV, "
          f"chi2/ndf={r['chi2']:.1f}/{r['ndf']}, valid={valid}")

    npz_path = res_dir / f"RUN{run_id}_{peak}.npz"
    np.savez(npz_path, run_id=np.int32(run_id), **r)

    fig, ax = plt.subplots(figsize=(9, 6))
    ftr.make_axes(ax, run_id, cfg["title"])
    plt.tight_layout()
    fig_path = fig_dir / f"RUN{run_id}_{peak}.png"
    fig.savefig(fig_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"result_npz": str(npz_path), "figure": str(fig_path),
            "mu": r["mu"], "mu_err": r["mu_err"], "fit_valid": valid,
            "sigma": r["sigma"], "chi2": r["chi2"], "ndf": r["ndf"]}


def fit_o16(prompt_energy: np.ndarray, run_id: int,
            res_dir: Path, fig_dir: Path) -> dict | None:
    """O16 6.13 MeV 模板分解 —— 复用 build_fitter('AmC') 原样调用。"""
    from MCBased_Fitter import build_fitter, filter_source_name
    source, fitter, plot_func, bins_fit, fit_args, zoom_xlim = build_fitter(
        "AmC", prompt_energy)
    print(f"[Info] O16 fitter: {len(bins_fit)-1} bins "
          f"{bins_fit[0]:.2f}-{bins_fit[-1]:.2f} MeV, "
          f"{len(prompt_energy)} prompt events")
    fitter.fit()
    sample_label = f"RUN{run_id}_{source}"
    npz_path = res_dir / f"{sample_label}.npz"
    np.savez(npz_path, **fitter.dict_result)

    fig_path = fig_dir / f"{sample_label}.pdf"
    plot_func(
        fitter,
        title_latex=f"{sample_label.replace('_', ' ')} "
                    f"$^{{{filter_source_name(source)}}}$ Fitting Result",
        fig_path=str(fig_path),
        ylabel_show="Event Rate [Hz/bin]",
        ylimit=fit_args.get("ylimit", 1e-5),
        if_show_ylog=True,
    )
    plt.close("all")
    cg = fitter.dict_result["center_gauss_6_13"]
    mu, mu_err = float(cg["value"]), float(cg["error"])
    valid = bool(fitter.minuit_core.valid)
    chi2 = float(fitter.dict_result.get("chi2", np.nan))
    ndf = int(fitter.dict_result.get("ndf", 0))
    sigma = float(fitter.dict_result["sigma_gauss_6_13"]["value"])
    print(f"RUN{run_id} O16: center_gauss_6_13 = {mu:.4f} ± {mu_err:.4f} MeV "
          f"(minuit valid={valid}, chi2/ndf={chi2:.0f}/{ndf})")
    if not valid or mu_err <= 0:
        print("[Warning] O16 minuit errors unreliable (HESSE failed / param "
              "at limit). Point estimate is used; nlfit MU_ERR_FLOOR=0.005 "
              "applies downstream. See run_log.")
    return {"result_npz": str(npz_path), "figure": str(fig_path),
            "mu": mu, "mu_err": mu_err, "fit_valid": valid,
            "sigma": sigma, "chi2": chi2, "ndf": ndf}


def main() -> int:
    ap = argparse.ArgumentParser(description="AmC triple-peak fit (nH/nC/O16)")
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--corr-npz", required=True,
                    help="correlation_result_RUN{N}.npz from amcsel")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--peaks", default="nH,nC,AmC",
                    help="subset of peaks to fit (nH,nC,AmC)")
    ap.add_argument("--launched-by", default="script",
                    choices=["script", "agent"])
    ap.add_argument("--agent-name", default="")
    ap.add_argument("--agent-version", default="")
    ap.add_argument("--agent-workflow", default="")
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir) if args.out_dir else PROJECT_ROOT / "output" / ts
    res_dir, fig_dir = out / "results", out / "figures"
    res_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    peaks = [p.strip() for p in args.peaks.split(",") if p.strip()]
    print(f"[Info] Output directory: {out}")

    audit_failed = False
    with RunLogger(output_dir=out, project_root=_PROJ_ROOT,
                   launched_by=args.launched_by) as logger:
        logger.record_command(sys.argv)
        if args.launched_by == "agent" and args.agent_name:
            logger.set_agent_info(
                agent_name=args.agent_name,
                agent_version=args.agent_version,
                workflow_description=args.agent_workflow,
            )
        logger.save_config_snapshot(extra_configs={
            "amc_run": args.run,
            "corr_npz": args.corr_npz,
            "peaks": peaks,
        })
        _tee = logger.ConsoleTee(sys.stdout, logger)

        with contextlib.redirect_stdout(_tee):
            corr = Path(args.corr_npz)
            energies = load_amc_energies(corr)
            print(f"[Info] correlation npz keys: "
                  f"{ {k: len(v) for k, v in energies.items()} }")

            for peak in peaks:
                t0 = time.time()
                try:
                    if peak not in energies:
                        raise RuntimeError(
                            f"required key missing in {corr} (have "
                            f"{list(energies)})")
                    if peak in ("nH", "nC"):
                        rec = fit_gaussian_peak(peak, energies[peak],
                                                args.run, res_dir, fig_dir)
                        fitter_file = "src/NhnCFitter.py (ported nH_nC_fitter)"
                    else:  # AmC / O16
                        rec = fit_o16(energies["AmC"], args.run,
                                      res_dir, fig_dir)
                        fitter_file = "src/MCBased_Fitter.py build_fitter -> fitters/O16Fitter.py"
                    logger.add_source_record(
                        src_name=peak, run_id=args.run,
                        e_true=E_TRUE.get(peak, 0.0),
                        fitter_type="gaussian" if peak in ("nH", "nC")
                                    else "o16-template",
                        fitter_file=fitter_file,
                        input_path=str(corr),
                        output_files=({"result_npz": rec["result_npz"],
                                       "figure": rec["figure"]}
                                      if rec else {}),
                        fit_results=({"mu": rec["mu"],
                                      "sigma": rec.get("sigma", 0.0),
                                      "sigma_over_e_pct":
                                          100.0 * rec.get("sigma", 0.0)
                                          / rec["mu"] if rec["mu"] else 0.0,
                                      "chi2": rec.get("chi2", 0.0),
                                      "ndf": rec.get("ndf", 0),
                                      "mu_err": rec["mu_err"],
                                      "fit_valid":
                                          bool(rec.get("fit_valid", False))}
                                     if rec else None),
                        elapsed_s=round(time.time() - t0, 1),
                        status="success" if rec else "skipped",
                        error_message=None if rec
                                       else "too few events in fit range",
                    )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    logger.add_source_record(
                        src_name=peak, run_id=args.run,
                        e_true=E_TRUE.get(peak, 0.0),
                        fitter_type="n/a", fitter_file="n/a",
                        input_path=str(corr), output_files={},
                        status="failed", error_message=str(e),
                        elapsed_s=round(time.time() - t0, 1),
                    )
                    logger.add_error(peak, str(e))
                    print(f"[Error] fit {peak} failed: {e}")
                    logger.set_exit_code(1)

            logger.set_summary({"run": args.run, "peaks": peaks,
                                "corr_npz": str(corr)})
            snap = logger.snapshot_code_full()
            # 记录文件由 RunLogger.finalize 落盘后经 _post_finalize_audit 复核，
            # 此处只审计本次运行的物理产物（与 run_fit_all 约定一致）
            expected = [out / "config_snapshot.json"]
            for peak in peaks:
                expected.append(res_dir / f"RUN{args.run}_{peak}.npz")
            audit = logger.run_audit(expected)
            if audit["passed"]:
                print(f"[AUDIT] PASSED ({snap['n_files']} code files, "
                      f"outputs complete)")
            else:
                logger.add_error("audit",
                                 f"audit failed: missing="
                                 f"{audit['outputs']['missing'][:4]}")
                logger.record["status"] = "audit-failed"
                if args.launched_by == "agent":
                    print("[AUDIT] WARNING: completeness audit FAILED")
                else:
                    print(f"[AUDIT] FAILED: missing "
                          f"{audit['outputs']['missing'][:4]}. Exit 3.")
                    audit_failed = True
            logger.set_exit_code(3 if audit_failed else 0)

    print(f"\n[Info] AmC fit complete. Output: {out}")
    return 3 if audit_failed else 0


if __name__ == "__main__":
    sys.exit(main())
