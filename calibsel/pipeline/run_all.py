#!/usr/bin/env python3
"""
run_all.py — one-click orchestration of the standalone_calibsel pipeline.

Default mode ("from-edm", the old --skip-esd): start from the pre-existing
ReProd26B EDM chunks on lustrefs and run, per calibration run:

    Stage 1  EDM -> NPZ            src/convert_edm_to_npz.py
    Stage 2  26B Finalcorrection   src/apply_final_correction.py
    Stage 2b background run (auto) stages 1-2 for the mapped physics run
    Stage 3  singles selection     src/combine_selection.py   (cuts!)
    Stage 4  physics QA figures    tools/make_physics_qa.py

Optional "full-esd" mode additionally runs Stage 0 (ESD -> EDM, needs the
external JUNO CVMFS/JUNOSW environment; see config/paths.py).

Every run is fully archived under output/<timestamp>/ with run_log.{md,json}
(schema 2.0: pipeline_metadata incl. exit_code/errors/packages/pip_freeze/
config fingerprints, per-run records with run_info + event_statistics +
input/output fingerprints), config_snapshot.json, console.log,
code_snapshot/ (sha256 of the algorithm files that define the cuts) and
cuts/ (the runtime cut values).

Usage:
    python pipeline/run_all.py                      # DEFAULT_RUNS, from-edm
    python pipeline/run_all.py --runs 12370 12295
    python pipeline/run_all.py --full-esd           # + ESD reconstruction
    python pipeline/run_all.py --full-esd --slice 3 # smoke test, 3 ESD files
    python pipeline/run_all.py --edm-input <DIR>    # custom EDM chunks
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ / "config"))
sys.path.insert(0, str(_PROJ / "pipeline"))

os.environ.setdefault("MPLCONFIGDIR", str(_PROJ / "TMP" / "matplotlib"))

import paths  # noqa: E402
from run_logger import RunLogger, file_info, sha256_file  # noqa: E402
from cuts_parser import write_cuts_record  # noqa: E402

PY = sys.executable


# ---------------------------------------------------------------- helpers
def bkg_run_of(run: int):
    """Source,PhysicsRun mapping from calib_to_analyze.txt."""
    with open(paths.CALIB_INFO_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Source"):
                continue
            p = [x.strip() for x in line.split(",")]
            if len(p) < 3 or "-" not in p[1]:
                continue
            a, b = p[1].split("-")[:2]
            try:
                if int(a) <= run <= int(b):
                    return p[2]
            except ValueError:
                continue
    return None


def run_info_of(run: int) -> dict:
    """Run -> {source,date,x_m,y_m,z_m,r_m} from CalibRUN_from_file.csv."""
    if not os.path.exists(paths.CALIB_POS_FILE):
        return {}
    with open(paths.CALIB_POS_FILE) as f:
        for row in csv.DictReader(f):
            try:
                if int(row["RUN"]) == run:
                    return {
                        "run": run,
                        "source": row.get("Source", ""),
                        "date": row.get("Date", ""),
                        "x_m": float(row.get("X[m]", "nan")),
                        "y_m": float(row.get("Y[m]", "nan")),
                        "z_m": float(row.get("Z[m]", "nan")),
                        "r_m": float(row.get("R[m]", "nan")),
                    }
            except (KeyError, ValueError):
                continue
    return {}


def event_statistics_of(npz_path: Path) -> dict:
    """Event statistics + 200-bin pre-selection spectrum (mirrors fitter)."""
    import numpy as np
    try:
        with np.load(npz_path, allow_pickle=True) as d:
            e = d["omilrec_energy"].astype(np.float64)
    except Exception as ex:
        return {"error": str(ex)}
    finite = np.isfinite(e)
    counts, edges = np.histogram(e[finite], bins=200, range=(0.0, 3.0))
    return {
        "total_events": int(e.size),
        "finite_events": int(finite.sum()),
        "energy_min": float(e[finite].min()) if finite.any() else None,
        "energy_max": float(e[finite].max()) if finite.any() else None,
        "energy_mean": float(e[finite].mean()) if finite.any() else None,
        "energy_median": float(np.median(e[finite])) if finite.any() else None,
        "pre_selection_spectrum": {
            "bin_edges_full": [float(x) for x in edges],
            "counts": [int(x) for x in counts],
        },
    }


def run_stage(cmd: list[str], log_path: Path):
    """Run one stage, tee output to its log file; return (rc, output, seconds)."""
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    t0 = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as fh:
        proc = subprocess.run(
            [str(c) for c in cmd], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, cwd=str(_PROJ))
        out = proc.stdout or ""
        fh.write(out)
    for line in out.splitlines():
        print(f"  {line}", flush=True)
    return proc.returncode, out, round(time.time() - t0, 1)


def edm_input_for(run: int, mode: str, edm_input: str | None,
                  local_edm: Path) -> str | None:
    """Resolve the EDM chunk directory for a run."""
    if edm_input:
        return edm_input
    if mode == "full-esd" and any(local_edm.glob(f"run_{run}_*.root")):
        return str(local_edm)
    if paths.REMOTE_EDM_DIR.is_dir():
        return str(paths.REMOTE_EDM_DIR)
    return None


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--runs", type=int, nargs="*", default=None,
                    help=f"calibration run numbers (default: {paths.DEFAULT_RUNS})")
    ap.add_argument("--full-esd", action="store_true",
                    help="run Stage 0 ESD->EDM first (needs CVMFS/JUNOSW); "
                         "default is to start from the pre-existing EDM")
    ap.add_argument("--esd-list-dir", default=None,
                    help="take ESD file lists from <dir>/esd_list_<RUN>.txt "
                         "(written by the recon module) instead of querying "
                         "EOS production; implies Stage 0 ESD->EDM")
    ap.add_argument("--slice", type=int, default=None,
                    help="with --full-esd: reconstruct only the first N ESD files")
    ap.add_argument("--edm-input", default=None,
                    help="override EDM chunk directory")
    ap.add_argument("--skip-bkg", action="store_true",
                    help="do not auto-process the background run")
    ap.add_argument("--skip-qa", action="store_true",
                    help="skip the physics QA figure stage")
    ap.add_argument("--out-dir", default=None,
                    help="output root (default: output/<timestamp>); when given, "
                         "writes directly into this directory (no nested timestamp)")
    ap.add_argument("--launched-by", default="script", choices=["script", "agent"])
    args = ap.parse_args()

    runs = args.runs or list(paths.DEFAULT_RUNS)
    # --esd-list-dir (recon module handoff) implies the full-esd Stage 0
    mode = "full-esd" if (args.full_esd or args.esd_list_dir) \
        else paths.DEFAULT_MODE

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir) if args.out_dir else paths.OUTPUT_DIR / ts
    res_npz_raw = out / "results" / "npz_raw"
    res_npz_corr = out / "results" / "npz_corrected"
    res_sel_npz = out / paths.SELECTION_NPZ_SUBDIR
    res_ts = out / "results" / "timestamps"
    fig_sel = out / "figures" / "selection"
    fig_qa = out / "figures" / "physics_qa"
    logs = out / "logs"
    work = out / "_work"
    for d in (res_npz_raw, res_npz_corr, res_sel_npz, res_ts, fig_sel, fig_qa, logs):
        d.mkdir(parents=True, exist_ok=True)

    print(f"[Info] Output directory: {out}")
    print(f"[Info] Mode: {mode}   runs: {runs}")

    failed = False
    with RunLogger(output_dir=out, project_root=_PROJ,
                   launched_by=args.launched_by) as logger:
        tee_out = logger.ConsoleTee(sys.stdout, logger)
        with contextlib.redirect_stdout(tee_out):
            logger.set_pipeline_info(
                mode=mode, runs=runs, edm_input=args.edm_input or "auto",
                remote_edm_dir=str(paths.REMOTE_EDM_DIR),
                slice=args.slice, skip_bkg=args.skip_bkg)
            logger.snapshot_code()
            logger.snapshot_config()

            for run in runs:
                rec = {"run": run, "stages": [], "outputs": [], "status": "ok"}
                ri = run_info_of(run)
                rec["source"] = ri.get("source")
                rec["run_info"] = ri

                def stage(status, name, dt, detail=None, run_id=None):
                    rec["stages"].append({
                        "stage": name,
                        "run": run_id if run_id is not None else run,
                        "status": status,
                        "elapsed_s": dt, "detail": detail or {},
                    })

                # ---------------- Stage 0 (optional) ----------------
                if mode == "full-esd":
                    if args.esd_list_dir:
                        # ESD lists handed over by the recon module
                        # (local reconstruction); no EOS query needed.
                        esd_list = Path(args.esd_list_dir) / f"esd_list_{run}.txt"
                        if not esd_list.exists():
                            print(f"[Error] missing recon handoff {esd_list}")
                            stage("failed", "0a esd-list", 0,
                                  {"source": "recon handoff"})
                            logger.add_error(
                                "stage0a", f"RUN{run}: missing {esd_list}")
                            failed = True
                            break
                        stage("ok", "0a esd-list", 0,
                              {"source": "recon handoff"})
                    else:
                        esd_list = _PROJ / f"esd_list_{run}.txt"
                        if not esd_list.exists():
                            rc, o, dt = run_stage(
                                [PY, _PROJ / "src/list_esd.py", run,
                                 "--out", esd_list], logs / f"stage0a_{run}.log")
                            stage("ok" if rc == 0 else "failed", "0a esd-list", dt)
                            if rc:
                                failed = True
                                break
                    cmd = [PY, _PROJ / "src/esd_to_edm.py", run,
                           "--esd-list", esd_list]
                    if args.slice:
                        cmd += ["--start", 0, "--end", args.slice - 1]
                    rc, o, dt = run_stage(cmd, logs / f"stage0b_{run}.log")
                    stage("ok" if rc == 0 else "failed", "0b esd->edm", dt)
                    if rc:
                        failed = True
                        break

                # ---------------- Stage 1 + 2 (calib & bkg) ----------------
                todo = [run]
                bkg = None
                if not args.skip_bkg:
                    bkg_txt = bkg_run_of(run)
                    if bkg_txt and bkg_txt.isdigit():
                        bkg = int(bkg_txt)
                        bkg_corr = res_npz_corr / f"RUN{bkg}.npz"
                        if not bkg_corr.exists():
                            todo.append(bkg)

                for r in todo:
                    edm_dir = edm_input_for(r, mode, args.edm_input,
                                            paths.EDM_DIR)
                    if not edm_dir:
                        print(f"[Error] no EDM data for RUN {r}")
                        stage("failed", "1 edm->npz", 0,
                              {"detail": "no EDM input"}, run_id=r)
                        logger.add_error("stage1", f"RUN{r}: no EDM input")
                        failed = True
                        break
                    rc, o, dt = run_stage(
                        [PY, _PROJ / "src/convert_edm_to_npz.py",
                         "--run", r, "--input-dir", edm_dir,
                         "--out-dir", res_npz_raw],
                        logs / f"stage1_{r}.log")
                    n_chunks = 0
                    if os.path.isdir(edm_dir):
                        n_chunks = len(list(Path(edm_dir).glob(f"run_{r}_*.root")))
                    stage("ok" if rc == 0 else "failed", "1 edm->npz", dt,
                          {"edm_dir": edm_dir, "n_chunks": n_chunks},
                          run_id=r)
                    if rc:
                        failed = True
                        break
                    raw_npz = res_npz_raw / f"RUN{r}.npz"
                    cur_events = event_statistics_of(raw_npz)
                    cur_input = {
                        "edm_dir": edm_dir,
                        "n_chunks": n_chunks,
                        "raw_npz": file_info(raw_npz),
                    }

                    rc, o, dt = run_stage(
                        [PY, _PROJ / "src/apply_final_correction.py", r,
                         "--input", raw_npz, "--out-dir", res_npz_corr],
                        logs / f"stage2_{r}.log")
                    detail = {}
                    m = re.search(r"phase=(\d+)", o)
                    if m:
                        detail["phase"] = int(m.group(1))
                    m = re.search(r"absolute_scale=([\d.]+)", o)
                    if m:
                        detail["absolute_scale"] = float(m.group(1))
                    stage("ok" if rc == 0 else "failed", "2 finalcorrection", dt,
                          detail, run_id=r)
                    if rc:
                        failed = True
                        break
                    corr_npz = res_npz_corr / f"RUN{r}.npz"
                    out_fp = [
                        {"path": str(raw_npz), "kind": "npz_raw",
                         **file_info(raw_npz)},
                        {"path": str(corr_npz), "kind": "npz_corrected",
                         **file_info(corr_npz)},
                    ]
                    if r == run:
                        rec["event_statistics"] = cur_events
                        rec["input"] = cur_input
                        rec["outputs"] += out_fp
                    else:
                        # background run: independent record (no selection)
                        bkg_rec = {
                            "run": r, "source": f"bkg-of-{run}",
                            "status": "ok",
                            "run_info": run_info_of(r),
                            "input": cur_input,
                            "event_statistics": cur_events,
                            "stages": [s for s in rec["stages"]
                                       if s["run"] == r],
                            "outputs": out_fp,
                        }
                        logger.add_run(**bkg_rec)
                        rec["stages"] = [s for s in rec["stages"]
                                         if s["run"] != r]
                if failed:
                    logger.add_run(**{**rec, "status": "failed"})
                    break

                # ---------------- Stage 3: selection (cuts) ----------------
                sel_work = work / f"selection_{run}"
                rc, o, dt = run_stage(
                    [PY, _PROJ / "src/combine_selection.py", run,
                     "--Finalcorrection",
                     "--input-dir", res_npz_corr,
                     "--out-dir", sel_work],
                    logs / f"stage3_{run}.log")
                cuts = write_cuts_record(out, run, o) if rc == 0 else {}
                stage("ok" if rc == 0 else "failed", "3 selection", dt,
                      {"cuts_file": f"cuts/{run}_cuts.json"})
                if rc:
                    failed = True
                    logger.add_run(**{**rec, "status": "failed"})
                    break
                rec["cuts_ref"] = f"cuts/{run}_cuts.json"

                # harvest deliverables out of the selection work dir
                for src in sel_work.rglob("*"):
                    if not src.is_file():
                        continue
                    rel = src.relative_to(sel_work)
                    if rel.as_posix().startswith("npz/"):
                        dst = res_sel_npz / rel.name
                    elif rel.as_posix().startswith("Timestamp"):
                        dst = res_ts / rel.parent / rel.name
                    elif src.suffix == ".png":
                        dst = fig_sel / rel.name
                    else:
                        continue
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    rec["outputs"].append(
                        {"path": str(dst), "kind": f"selection {rel}",
                         **file_info(dst)})
                shutil.rmtree(sel_work, ignore_errors=True)
                while work.exists() and not any(work.iterdir()):
                    work.rmdir()

                # ---------------- Stage 4: physics QA ----------------
                if not args.skip_qa:
                    sel_npz = res_sel_npz / f"Run{run}_SelectionResult.npz"
                    rc, o, dt = run_stage(
                        [PY, _PROJ / "tools/make_physics_qa.py", "--run", run,
                         "--corrected-dir", res_npz_corr,
                         "--selection-npz", sel_npz,
                         "--out-dir", fig_qa],
                        logs / f"stage4_qa_{run}.log")
                    stage("ok" if rc == 0 else "failed", "4 physics-qa", dt)
                    for suffix, kind in (("png", "physics_qa"),
                                         ("json", "physics_qa_json")):
                        qa_f = fig_qa / f"Run{run}_physics_qa.{suffix}"
                        if qa_f.exists():
                            rec["outputs"].append(
                                {"path": str(qa_f), "kind": kind,
                                 **file_info(qa_f)})

                logger.add_run(**rec)

            # ---- end-of-run audit: full code snapshot + output completeness ----
            snap = logger.snapshot_code_full()
            expected = [out / "run_log.json", out / "run_log.md",
                        out / "config_snapshot.json", out / "console.log",
                        out / "code" / "sha256.json"]
            for run in runs:
                expected += [
                    out / "cuts" / f"{run}_cuts.json",
                    out / paths.SELECTION_NPZ_SUBDIR / f"Run{run}_SelectionResult.npz",
                    out / "figures" / "selection" / f"Run{run}_1_SelectionPlot.png",
                    out / "results" / "npz_raw" / f"RUN{run}.npz",
                    out / "results" / "npz_corrected" / f"RUN{run}.npz",
                ]
                if not args.skip_bkg:
                    bkg = bkg_run_of(run)
                    if bkg and bkg.isdigit():
                        b = int(bkg)
                        expected += [
                            out / "results" / "npz_raw" / f"RUN{b}.npz",
                            out / "results" / "npz_corrected" / f"RUN{b}.npz",
                        ]
            audit = logger.run_audit(expected)
            audit_ok = bool(audit["passed"])
            audit_failed = False
            if audit_ok:
                print(f"[AUDIT] PASSED ({snap['n_files']} code files, "
                      f"outputs complete)")
            else:
                cs, oo = audit["code_snapshot"], audit["outputs"]
                logger.add_error(
                    "audit",
                    f"completeness audit failed: code all_match={cs['all_match']}"
                    f" (missing={len(cs['missing'])}, mismatched={len(cs['mismatched'])},"
                    f" extra={len(cs['extra'])}), outputs all_present={oo['all_present']}"
                    f" (missing={oo['missing'][:4]})")
                if args.launched_by == "agent":
                    print("[AUDIT] WARNING: code/output completeness audit FAILED. "
                          "Agent, review run_log.json -> audit before using outputs.")
                    logger.data["status"] = "audit-failed"
                else:
                    print("[AUDIT] FAILED: code/output completeness audit failed "
                          f"(missing outputs: {oo['missing'][:4]}; "
                          f"code mismatches: {cs['mismatched'][:3]}). "
                          "Pipeline will exit with code 3.")
                    audit_failed = True

            # ---- publish latest only when everything is complete ----
            if not failed and audit_ok and not args.out_dir:
                latest_link = paths.OUTPUT_DIR / "latest"
                tmp_link = paths.OUTPUT_DIR / ".latest.tmp"
                if tmp_link.is_symlink() or tmp_link.exists():
                    tmp_link.unlink()
                tmp_link.symlink_to(out, target_is_directory=True)
                os.replace(tmp_link, latest_link)
                logger.set_pipeline_info(latest_symlink=str(latest_link),
                                         latest_target=str(out))

            if failed:
                logger.set_exit_code(1)
            elif audit_failed:
                logger.set_exit_code(3)
            else:
                logger.set_exit_code(0)

    print()
    print("[Info] Pipeline", "FAILED" if failed else "complete.")
    print(f"[Info] Output directory: {out}")
    if not failed and audit_ok and not args.out_dir:
        print(f"[Info] Published as: {paths.OUTPUT_DIR / 'latest'}")
    print(f"[Info] Selection NPZ (fitter input): {res_sel_npz}")
    print(f"[Info] Cut conditions: {out / 'cuts'}")
    return 3 if (not failed and audit_failed) else (1 if failed else 0)


if __name__ == "__main__":
    sys.exit(main())
