#!/usr/bin/env python3
"""
run_recon_all.py — recon 模块编排入口（Stage −1: rtraw → ESD）。

对每个 run：
    Stage -1pre  verify  校验 OMILREC 四件套 map/PDF 的 sha256（数据漂移守门）
    Stage -1a    list    list_rtraw.py 生成 rtraw 输入清单（xrootd URL）
    Stage -1b    recon   rtraw_to_esd.py：CVMFS J26.1.1 环境下跑官方
                        tut_rtraw2rec（--impl omilrecv2 时叠加 OMILRECV2
                        overlay），并校验产物含 CdVertexRecOMILREC 事例
    handoff       写 results/esd_lists/esd_list_<N>.txt（本地 ESD 路径），
                        供 calibsel Stage 0（MySimpleTag）--esd-list-dir 使用

纯编排：重建本身一行不改；flag 集冻结于 config/paths.py（见 PROVENANCE.md）。
无需 venv（仅标准库；重建在 wrapper 内用 CVMFS python 跑）。

Usage:
    python3 pipeline/run_recon_all.py --runs 10110 \
        [--impl omilrecv2|baseline] [--slice 1] [--evtmax 100] \
        [--out-dir <dir>] [--launched-by script|agent]
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import subprocess
import sys
import time
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
for _p in ("config", "src", "pipeline"):
    if str(_PROJ / _p) not in sys.path:
        sys.path.insert(0, str(_PROJ / _p))

import config.paths as P  # noqa: E402
from run_logger import RunLogger  # noqa: E402

PY = sys.executable


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_map_assets() -> list[str]:
    """Return list of problems ([] = ok) for the four OMILREC map assets."""
    problems = []
    for rel, expected in P.MAP_ASSETS.items():
        p = P.MAPS_DIR / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif sha256_of(p) != expected:
            problems.append(f"sha256 mismatch {rel}")
    return problems


def run_info_of(run: int) -> dict:
    """run -> date/source/position from calibsel's csv (read-only)."""
    with open(P.CALIB_POS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            if row["RUN"].strip() == str(run):
                return {k: row[k].strip() for k in row}
    return {}


def run_stage(cmd: list, log: Path):
    t0 = time.time()
    with open(log, "w") as lf:
        rc = subprocess.call(cmd, stdout=lf, stderr=subprocess.STDOUT)
    return rc, time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--runs", type=int, nargs="+", default=[P.TEST_RUN])
    ap.add_argument("--impl", choices=["omilrecv2", "baseline"],
                    default=P.DEFAULT_IMPL)
    ap.add_argument("--slice", type=int, default=P.DEFAULT_SLICE,
                    help="rtraw files per run (default 1 = smoke-scale)")
    ap.add_argument("--evtmax", type=int, default=P.DEFAULT_EVTMAX,
                    help="events per run (-1 = all)")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--launched-by", default="script",
                    choices=["script", "agent"])
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_dir) if args.out_dir else P.OUTPUT_DIR / ts
    res_esd = out / P.ESD_SUBDIR
    res_lists = out / P.ESD_LIST_SUBDIR
    logs = out / "logs"
    work = out / "_work"
    for d in (res_esd, res_lists, logs, work):
        d.mkdir(parents=True, exist_ok=True)

    print(f"[Info] recon impl={args.impl} runs={args.runs} "
          f"slice={args.slice} evtmax={args.evtmax}")
    print(f"[Info] Output directory: {out}")

    failed = False
    with RunLogger(output_dir=out, project_root=_PROJ,
                   launched_by=args.launched_by) as logger:
        tee = logger.ConsoleTee(sys.stdout, logger)
        with contextlib.redirect_stdout(tee):
            logger.set_pipeline_info(
                impl=args.impl, runs=args.runs, slice=args.slice,
                evtmax=args.evtmax, global_tag=P.GLOBAL_TAG,
                omilrecv2_dir=str(P.OMILRECV2_DIR),
                maps_dir=str(P.MAPS_DIR))
            logger.snapshot_code_full()
            logger.snapshot_config()

            # ---- Stage -1pre: map asset sha256 guard ----
            t0 = time.time()
            problems = verify_map_assets()
            pre_stages = [{
                "stage": "-1pre verify-maps", "run": 0,
                "status": "ok" if not problems else "failed",
                "elapsed_s": time.time() - t0,
                "detail": {"n_assets": len(P.MAP_ASSETS), "problems": problems},
            }]
            if problems:
                for p in problems:
                    logger.add_error("-1pre", p)
                logger.add_run(run=0, status="failed", stages=pre_stages)
                failed = True
            else:
                print(f"[Info] map assets verified ({len(P.MAP_ASSETS)} sha256 ok)")

            if not failed:
                for run in args.runs:
                    rec_stages = list(pre_stages)  # first run carries -1pre
                    pre_stages = []
                    ri = run_info_of(run)
                    rec = {"ok": True}

                    # ---- Stage -1a: rtraw list ----
                    rtraw_list = work / f"rtraw_list_{run}.txt"
                    rc, dt = run_stage(
                        [PY, _PROJ / "src" / "list_rtraw.py", str(run),
                         "--out", rtraw_list, "--slice", str(args.slice)],
                        logs / f"stage-1a_list_{run}.log")
                    n_files = len(rtraw_list.read_text().split()) \
                        if rtraw_list.exists() else 0
                    rec_stages.append({
                        "stage": "-1a rtraw-list", "run": run,
                        "status": "ok" if rc == 0 and n_files else "failed",
                        "elapsed_s": dt, "detail": {"n_files": n_files},
                    })
                    if rc != 0 or not n_files:
                        rec["ok"] = False

                    # ---- Stage -1b: rtraw -> ESD ----
                    esd_root = res_esd / f"RUN{run}" / f"recon_RUN{run}.root"
                    esd_root.parent.mkdir(parents=True, exist_ok=True)
                    if rec["ok"]:
                        rc, dt = run_stage(
                            [PY, _PROJ / "src" / "rtraw_to_esd.py", str(run),
                             "--input-list", rtraw_list,
                             "--out-root", esd_root,
                             "--evtmax", str(args.evtmax),
                             "--impl", args.impl,
                             "--work-dir", work],
                            logs / f"stage-1b_recon_{run}.log")
                        rec_stages.append({
                            "stage": "-1b rtraw->esd", "run": run,
                            "status": "ok" if rc == 0 else "failed",
                            "elapsed_s": dt,
                            "detail": {"esd_root": str(esd_root),
                                       "evtmax": args.evtmax},
                        })
                        if rc != 0:
                            rec["ok"] = False

                    # ---- handoff: esd list for calibsel Stage 0 ----
                    esd_list = res_lists / f"esd_list_{run}.txt"
                    if rec["ok"] and esd_root.exists():
                        esd_list.write_text(f"{esd_root}\n")
                        logger.add_output(esd_root, "esd_root")
                        logger.add_output(esd_list, "esd_list_handoff")
                        rec_stages.append({
                            "stage": "handoff esd-list", "run": run,
                            "status": "ok", "elapsed_s": 0.0,
                            "detail": {"esd_list": str(esd_list)},
                        })
                    else:
                        rec["ok"] = False
                        logger.add_error(str(run), "ESD not produced")

                    if not rec["ok"]:
                        failed = True
                    logger.add_run(
                        run=run,
                        status="ok" if rec["ok"] else "failed",
                        source=ri.get("Source"), run_info=ri,
                        stages=rec_stages,
                        outputs=[{"kind": "esd_root", "path": str(esd_root)},
                                 {"kind": "esd_list_handoff",
                                  "path": str(esd_list)}])

            # ---- audit ----
            expected = [out / "config_snapshot.json",
                        out / "run_log.md", out / "run_log.json"]
            for run in args.runs:
                expected.append(res_lists / f"esd_list_{run}.txt")
                expected.append(res_esd / f"RUN{run}" / f"recon_RUN{run}.root")
            audit = logger.run_audit(expected)
            logger.set_exit_code(0 if audit["passed"] else 3)

    print(f"[Info] {'AUDIT PASSED' if audit['passed'] else 'AUDIT FAILED'}"
          f" — run_log: {out / 'run_log.md'}")
    return 0 if audit["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
