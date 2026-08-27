#!/usr/bin/env python3
"""
run_nlfit_all.py — one-click orchestration of the nlfit module.

    Stage 4b  external-input contract validation (MANIFEST sha256)
    Stage 5   aggregate per-source μ → gamma_AllPhase.dat (+ sidecars)
              → figures/stage5_gamma_peaks.{png,pdf}
    Stage 6   dybmodel global NL fit (C++ wrap; capability-probed, skippable)
              → results/bestFit*, nl_curves.tsv, figures/stage6_nl_curves.*,
                figures/dybmodel/*.pdf
    Stage 7   E_rec → E_true inversion → results/Etrue_from_Erec_lookup.*
              → figures/stage7_inversion.{png,pdf}

Every run is archived (run_log.{md,json}, config_snapshot.json, console.log,
code/ + sha256.json) and ends with a completeness audit (exit 3 on failure
in script mode, warning in agent mode) — same contract as calibsel/fitter.

Usage:
    .venv/bin/python pipeline/run_nlfit_all.py \
        --fitter-results <dir with RUN{N}_{src}.npz> --out-dir <dir>
    extra: --skip-dybmodel (Stages 5+7-only smoke), --validate-ref
"""
from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
for _p in ("config", "src", "pipeline"):
    if str(_PROJ / _p) not in sys.path:
        sys.path.insert(0, str(_PROJ / _p))
os.environ.setdefault("MPLCONFIGDIR", str(_PROJ / "TMP" / "matplotlib"))

import config.paths as P  # noqa: E402
from src.run_logger import RunLogger, ConsoleTee  # noqa: E402
from src import aggregate, dybmodel_wrap, invert, plots  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="nlfit orchestrator")
    ap.add_argument("--fitter-results", default=str(P.FITTER_RESULTS_DIR),
                    help="directory containing RUN{N}_{src}.npz from fitter/")
    ap.add_argument("--out-dir", default=None,
                    help="output root (default: nlfit/output/<timestamp>)")
    ap.add_argument("--skip-dybmodel", action="store_true",
                    help="skip Stage 6/7 (contract+aggregation smoke only)")
    ap.add_argument("--validate-ref", action="store_true",
                    help="Stage 6: also compare bestFit against the "
                         "historical reference (behaviour lock)")
    ap.add_argument("--launched-by", default="script",
                    choices=["script", "agent"])
    ap.add_argument("--agent-name", default="")
    ap.add_argument("--agent-version", default="")
    ap.add_argument("--agent-workflow", default="")
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir) if args.out_dir else _PROJ / "output" / ts
    res_dir = out / P.OUTPUT_RES_DIR
    fig_dir = out / P.OUTPUT_FIG_DIR
    res_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Info] Output directory: {out}")

    audit_failed = False
    with RunLogger(out, _PROJ, launched_by=args.launched_by,
                   agent_name=args.agent_name,
                   agent_version=args.agent_version,
                   agent_workflow=args.agent_workflow) as logger:
        tee = ConsoleTee(sys.stdout, logger)
        with contextlib.redirect_stdout(tee):
            logger.record_command(sys.argv)
            logger.set_pipeline_info(fitter_results=args.fitter_results,
                                     skip_dybmodel=args.skip_dybmodel,
                                     validate_ref=args.validate_ref)
            logger.snapshot_config()
            logger.snapshot_code()

            stage5, curves, lookup = None, None, None

            # ---------------- Stage 4b: external contract ----------------
            t0 = time.time()
            try:
                ext = aggregate.validate_external_inputs()
                status = "ok" if ext["all_valid"] else "failed"
                print(f"[Stage4b] external inputs "
                      f"{'valid' if ext['all_valid'] else 'INVALID'}")
                logger.add_stage("4b external-contract", status,
                                 round(time.time() - t0, 1), detail=ext)
                if not ext["all_valid"]:
                    raise RuntimeError("external-input contract violated "
                                       "(sha256 mismatch) — aborting")
            except Exception as e:
                logger.add_stage("4b external-contract", "failed",
                                 round(time.time() - t0, 1),
                                 detail={"error": str(e)})
                logger.add_error("4b", str(e))
                print(f"[Error] Stage 4b failed: {e}")
                logger.set_exit_code(1)
                return 1

            # ---------------- Stage 5: aggregate ----------------
            t0 = time.time()
            try:
                stage5 = aggregate.aggregate_gamma_dat(
                    args.fitter_results, res_dir)
                plots.plot_stage5(stage5["peaks"], fig_dir)
                logger.add_stage(
                    "5 aggregate", "ok", round(time.time() - t0, 1),
                    detail={"gamma_dat": stage5["gamma_dat"],
                            "note": "; ".join(stage5["warnings"]) or "clean"},
                    outputs={"gamma_dat": stage5["gamma_dat"],
                             "table": stage5["table"]})
            except Exception as e:
                logger.add_stage("5 aggregate", "failed",
                                 round(time.time() - t0, 1),
                                 detail={"error": str(e)})
                logger.add_error("5", str(e))
                print(f"[Error] Stage 5 failed: {e}")
                logger.set_exit_code(1)
                return 1

            # ---------------- Stage 6: dybmodel wrap ----------------
            if args.skip_dybmodel:
                print("[Stage6] skipped (--skip-dybmodel)")
                logger.add_stage("6 dybmodel", "skipped",
                                 detail={"note": "--skip-dybmodel"})
            else:
                t0 = time.time()
                try:
                    fit = dybmodel_wrap.run_dybmodel(out,
                                                     stage5["gamma_dat"])
                    probe = dybmodel_wrap.probe()
                    curves = invert.parse_curves_tsv(
                        fit["harvested"]["nl_curves_tsv"])
                    plots.plot_stage6(curves, stage5["peaks"], fig_dir)
                    if args.validate_ref:
                        ref = (Path(P.DYBMODEL_SRC) / "output" / "results" /
                               f"bestFit_{P.DYB_TOY_KEY}.dat")
                        got = Path(fit["harvested"][f"bestFit_{P.DYB_TOY_KEY}.dat"])
                        detail_note = _compare_bestfit(got, ref)
                    else:
                        detail_note = (f"fit {fit['elapsed_s']}s, "
                                       f"{fit['n_dybmodel_plots']} plots")
                    logger.add_stage("6 dybmodel", "ok",
                                     round(time.time() - t0, 1),
                                     detail={"note": detail_note,
                                             "probe": probe,
                                             "input_sha256":
                                                 fit["input_sha256"]},
                                     outputs=fit["harvested"])
                except Exception as e:
                    logger.add_stage("6 dybmodel", "failed",
                                     round(time.time() - t0, 1),
                                     detail={"error": str(e)})
                    logger.add_error("6", str(e))
                    print(f"[Error] Stage 6 failed: {e}")
                    logger.set_exit_code(1)
                    return 1

            # ---------------- Stage 7: inversion ----------------
            if curves is None:
                print("[Stage7] skipped (no curves — Stage 6 skipped)")
                logger.add_stage("7 inversion", "skipped",
                                 detail={"note": "depends on Stage 6"})
            else:
                t0 = time.time()
                try:
                    lookup = invert.build_lookups(
                        f"{res_dir}/nl_curves.tsv", res_dir)
                    # plotting payload straight from the written npz
                    import numpy as np  # noqa: PLC0415
                    with np.load(lookup["lookup_npz"]) as d:
                        payload = {k: d[k] for k in d.files}
                    plots.plot_stage7(curves, payload, fig_dir)
                    logger.add_stage("7 inversion", "ok",
                                     round(time.time() - t0, 1),
                                     detail={"note": "lookup built"},
                                     outputs={"npz": lookup["lookup_npz"],
                                              "csv": lookup["lookup_csv"]})
                except Exception as e:
                    logger.add_stage("7 inversion", "failed",
                                     round(time.time() - t0, 1),
                                     detail={"error": str(e)})
                    logger.add_error("7", str(e))
                    print(f"[Error] Stage 7 failed: {e}")
                    logger.set_exit_code(1)
                    return 1

            # ---------------- summary + audit ----------------
            logger.set_summary({
                "stages_run": "4b,5" + (",6,7" if curves is not None else ""),
                "gamma_dat": stage5["gamma_dat"],
                "lookup": (lookup or {}).get("lookup_npz", "n/a"),
            })
            expected = [out / "run_log.json", out / "run_log.md",
                        out / "config_snapshot.json", out / "console.log",
                        out / "code" / "sha256.json",
                        res_dir / "gamma_AllPhase.dat",
                        res_dir / "meanEscaleEres_perPhase_CDcenter.dat",
                        res_dir / "gamma_AllPhase.dat.provenance.json",
                        fig_dir / "stage5_gamma_peaks.png"]
            if curves is not None:
                expected += [res_dir / "nl_curves.tsv",
                             res_dir / f"bestFit_{P.DYB_TOY_KEY}.dat",
                             res_dir / f"curves_{P.DYB_TOY_KEY}.root",
                             fig_dir / "stage6_nl_curves.png",
                             fig_dir / "stage7_inversion.png",
                             res_dir / "Etrue_from_Erec_lookup.npz"]
            audit = logger.run_audit(expected)
            if audit["passed"]:
                print(f"[AUDIT] PASSED ({logger.data['code_snapshot']['n_files']}"
                      f" code files, outputs complete)")
            else:
                logger.add_error(
                    "audit",
                    f"completeness audit failed: outputs missing="
                    f"{audit['outputs']['missing'][:4]}, "
                    f"code all_match={audit['code_snapshot']['all_match']}")
                logger.data["status"] = "audit-failed"
                if args.launched_by == "agent":
                    print("[AUDIT] WARNING: completeness audit FAILED — "
                          "review run_log.json -> audit before using outputs.")
                else:
                    print(f"[AUDIT] FAILED: missing "
                          f"{audit['outputs']['missing'][:4]}. Exit 3.")
                    audit_failed = True

    print(f"\n[Info] nlfit complete. Output: {out}")
    return 3 if audit_failed else 0


def _compare_bestfit(got: Path, ref: Path) -> str:
    """Positional numeric comparison of two bestFit dat files (the format
    is header-free: line 0 = chi2, then one 'value error' pair per line)."""
    def parse(p: Path):
        rows = []
        for ln in p.read_text().splitlines():
            parts = ln.split()
            if len(parts) >= 2:
                try:
                    rows.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue
        return rows
    g, r = parse(got), parse(ref)
    n = min(len(g), len(r))
    worst = max(((abs(g[i][0] - r[i][0]) / max(abs(r[i][0]), 1e-12), i)
                 for i in range(n)), default=(0.0, -1))
    note = (f"validate-ref: {n} param rows vs historical, "
            f"worst rel dev {worst[0]:.2e} (row {worst[1]})")
    print(f"[Stage6] {note}")
    return note


if __name__ == "__main__":
    sys.exit(main())
