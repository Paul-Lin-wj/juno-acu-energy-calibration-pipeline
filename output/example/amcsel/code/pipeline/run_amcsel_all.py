#!/usr/bin/env python3
"""
run_amcsel_all.py — amcsel（Stage 3c：AmC 等(prompt,delayed)关联对挑选）一键编排。

流程与原作者驱动 correlate_selection/test.py（2026-04-14 版）逐步一致，
仅把路径/CLI/留档换成仓库惯例（RunLogger 审计、--launched-by agent 标志）。
分析参数全部来自 config/paths.py（逐字节取自 test.py 原值）。

    Stage 1  run-info   RunManager 查 Source/BKG/位置
    Stage 2  load       BaseAnalyzer.load_data（刻度源 + 本底 npz）
    Stage 3  fv         optimize_fv_cuts + apply_fv_selection
    Stage 4  correlate  set_parameters（中子源/普通源两组原值）
                        + find_correlated_events + fit_capture_time
              (cs137)   AmC-Cs137/Cs137 源：孤立事例挑选
    Stage 5  save       save_timestamps + plot_correlation_results
                        + save_correlation_results
                        → correlation_result_RUN{N}.npz（供 fitter 三峰拟合）

Usage:
    .venv/bin/python pipeline/run_amcsel_all.py --run 10104 \
        [--input-dir <Finalcorrection npz 目录>] [--out-dir <dir>]
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
from run_logger import RunLogger, ConsoleTee  # noqa: E402

# 原作者模块 —— 除 import 行本地化外逐字节原样（见 PROVENANCE.md）
from config_manager import AnalysisConfig  # noqa: E402
from run_manager import RunManager  # noqa: E402
from correlation_analyzer import CorrelationAnalyzer  # noqa: E402


def build_config(run_id: int, input_dir: Path, out_dir: Path) -> AnalysisConfig:
    """以仓库路径构造原作者的 AnalysisConfig（不改其任何默认行为）。"""
    return AnalysisConfig(
        input_data_path=str(input_dir),
        calib_info_file=str(P.CALIB_INFO_FILE),
        calib_pos_file=str(P.CALIB_POS_FILE),
        output_base_dir=str(out_dir / P.OUTPUT_RES_DIR / f"RUN{run_id}"),
        timestamp_dir=str(out_dir / "timestamps"),
        vertex_chose=P.VERTEX_ALGO,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="amcsel orchestrator")
    ap.add_argument("--run", type=int, required=True, help="RUN number")
    ap.add_argument("--input-dir", default=str(P.INPUT_DATA_DIR),
                    help="directory with Finalcorrection RUN<N>.npz (+BKG)")
    ap.add_argument("--out-dir", default=None,
                    help="output root (default: amcsel/output/<timestamp>)")
    ap.add_argument("--launched-by", default="script",
                    choices=["script", "agent"])
    ap.add_argument("--agent-name", default="")
    ap.add_argument("--agent-version", default="")
    ap.add_argument("--agent-workflow", default="")
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir) if args.out_dir else P.OUTPUT_DIR / ts
    input_dir = Path(args.input_dir)

    audit_failed = False
    with RunLogger(out, _PROJ, launched_by=args.launched_by,
                   agent_name=args.agent_name,
                   agent_version=args.agent_version,
                   agent_workflow=args.agent_workflow) as logger:
        tee = ConsoleTee(sys.stdout, logger)
        with contextlib.redirect_stdout(tee):
            logger.record_command(sys.argv)
            logger.set_pipeline_info(run=args.run, input_dir=str(input_dir))
            logger.snapshot_config()
            logger.snapshot_code()

            # ---------------- Stage 1: run info ----------------
            t0 = time.time()
            config = build_config(args.run, input_dir, out)
            run_mgr = RunManager(config)
            run_info = run_mgr.get_run_info(args.run)
            if run_info is None:
                logger.add_stage("1 run-info", "failed",
                                 round(time.time() - t0, 1),
                                 detail={"error": f"run {args.run} not in "
                                                  f"{P.CALIB_INFO_FILE}"})
                logger.add_error("1", f"run {args.run} not found in calib info")
                logger.set_exit_code(1)
                return 1
            config.calib_type = run_info["Source"]
            config.calib_type_short = run_info["Source"]
            config.BKG_run = run_info["BKG_RUN"]
            print(f"[Stage1] RUN {args.run}: Source={run_info['Source']} "
                  f"BKG={run_info['BKG_RUN']} "
                  f"pos=({run_info['X(cm)']:.1f},{run_info['Y(cm)']:.1f},"
                  f"{run_info['Z(cm)']:.1f}) cm")
            logger.add_stage("1 run-info", "ok", round(time.time() - t0, 1),
                             detail={"source": run_info["Source"],
                                     "bkg_run": run_info["BKG_RUN"],
                                     "position_cm": [run_info["X(cm)"],
                                                     run_info["Y(cm)"],
                                                     run_info["Z(cm)"]]})

            # ---------------- Stage 2: load ----------------
            t0 = time.time()
            analyzer = CorrelationAnalyzer(config, args.run)
            analyzer.set_run_info(run_info)
            analyzer.fv_energy_region = P.FV_ENERGY_REGION
            if not analyzer.load_data():
                logger.add_stage("2 load", "failed", round(time.time() - t0, 1))
                logger.add_error("2", "load_data returned False")
                logger.set_exit_code(1)
                return 1
            logger.add_stage("2 load", "ok", round(time.time() - t0, 1),
                             detail={"input_dir": str(input_dir),
                                     "bkg_run": run_info["BKG_RUN"]})

            # ---------------- Stage 3: FV ----------------
            t0 = time.time()
            print("[Stage3] optimizing standard FV cuts ...")
            analyzer.optimize_fv_cuts(output_pdf=True)
            analyzer.apply_fv_selection()
            analyzer.save_fv_cuts()  # 原作者方法；编排补调以归档切割条件
            logger.add_stage("3 fv", "ok", round(time.time() - t0, 1))

            # ---------------- Stage 4: correlation ----------------
            t0 = time.time()
            src = config.calib_type
            params = (P.PARAMS_NEUTRON if ("Am" in src or "Cf" in src)
                      else P.PARAMS_STANDARD)
            print(f"[Stage4] mode={'neutron' if params is P.PARAMS_NEUTRON else 'standard'}"
                  f" params={params}")
            analyzer.set_parameters(**params)
            correlation_result = None
            if src in P.SOURCES_DO_CORRELATION:
                correlation_result = analyzer.find_correlated_events()
            else:
                print(f"[Stage4] source '{src}' not in correlation list, skip")
            if src in P.SOURCES_DO_CS137:
                print(f"[Stage4] Cs137 isolation ±{P.CS137_ISOLATION_TIME}us, "
                      f"cut Peak+{P.CS137_ENERGY_STD_CUT}*Std")
                analyzer.find_cs137_events(
                    isolation_time=P.CS137_ISOLATION_TIME,
                    n_std_cut=P.CS137_ENERGY_STD_CUT)
            logger.add_stage("4 correlate", "ok", round(time.time() - t0, 1),
                             detail={"params": params,
                                     "correlated": correlation_result is not None})

            # ---------------- Stage 5: save ----------------
            t0 = time.time()
            if correlation_result or getattr(analyzer, "cs137_result", None):
                analyzer.save_timestamps()
                if correlation_result:
                    analyzer.fit_capture_time()
                    analyzer.plot_correlation_results(output_pdf=True)
                analyzer.save_correlation_results()
            else:
                print("[Warning] no correlated or single events found")
            corr_npz = (Path(config.select_result_path) /
                        f"correlation_result_RUN{args.run}.npz")
            stage5_ok = (not src in P.SOURCES_DO_CORRELATION) or corr_npz.is_file()
            logger.add_stage("5 save", "ok" if stage5_ok else "failed",
                             round(time.time() - t0, 1),
                             outputs={"correlation_result": str(corr_npz)})
            if not stage5_ok:
                logger.add_error("5", "correlation_result npz missing")
                logger.set_exit_code(1)
                return 1

            # ---------------- summary + audit ----------------
            npz_data = {}
            if corr_npz.is_file():
                import numpy as np  # noqa: PLC0415
                with np.load(corr_npz, allow_pickle=True) as d:
                    npz_data = {k: int(len(d[k])) for k in d.files}
            logger.set_summary({
                "run": args.run, "source": src,
                "bkg_run": run_info["BKG_RUN"],
                "correlation_result": str(corr_npz),
                "n_events_per_key": npz_data,
            })
            expected = [out / "run_log.json", out / "run_log.md",
                        out / "config_snapshot.json", out / "console.log",
                        out / "code" / "sha256.json",
                        Path(config.select_result_path) /
                        f"xyz_distribution_RUN{args.run}.pdf",
                        Path(config.select_result_path) /
                        f"fv_cuts_RUN{args.run}.npz",
                        out / "timestamps"]
            if corr_npz.is_file():
                expected += [corr_npz,
                             Path(config.select_result_path) /
                             f"Correlation_RUN{args.run}.pdf"]
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

    print(f"\n[Info] amcsel complete. Output: {out}")
    return 3 if audit_failed else 0


if __name__ == "__main__":
    sys.exit(main())
