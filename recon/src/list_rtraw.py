#!/usr/bin/env python3
"""
list_rtraw.py
=============
Stage -1a: build the rtraw input list for a calibration run.

Search order (xrootd/EOS, reachable from this host):
  1. DAQ daily archive   /eos/juno/rtraw/<YYYY>/<MMDD>/RUN.<N>.*.rtraw
     (date from calibsel's CalibRUN_from_file.csv)
  2. curated per-version area
     /eos/juno/juno-rtraw/<VER>/global_trigger/<NN000>/<NNN00>/<N>/

Output: a plain-text list of xrootd URLs, one per line — the native
`--input-list` format of tut_rtraw2rec.py (no per-entry json needed).

Usage:
    python3 src/list_rtraw.py 10110 --out esd_lists/../rtraw_10110.txt [--slice 1]
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

_PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJ))
import config.paths as P  # noqa: E402


def run_date_of(run: int) -> str:
    """'2025-09-12' from calibsel's run/position csv (read-only)."""
    with open(P.CALIB_POS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            if row["RUN"].strip() == str(run):
                return row["Date"].strip()
    raise SystemExit(f"[Error] RUN {run} not found in {P.CALIB_POS_FILE}")


def xrdfs_ls(path: str) -> list[str]:
    """Return the full listing of an EOS dir (empty list if missing)."""
    r = subprocess.run([P.XRDFS_BIN, P.XRDFS_HOST, "ls", path],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not r.stdout.strip():
        return []
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


def find_rtraw(run: int) -> tuple[str, list[str]]:
    """Return (where, files) with xrootd:// URLs for the run's rtraw files."""
    # 1. DAQ daily archive (flat by date)
    date = run_date_of(run)                    # 2025-09-12
    yyyy, mmdd = date.split("-")[0], date[5:].replace("-", "")
    daily = f"{P.RTRAW_DAILY_BASE}/{yyyy}/{mmdd}"
    pat = re.compile(rf"/RUN\.{run}\.[^/]*\.rtraw$")
    hits = [ln for ln in xrdfs_ls(daily) if pat.search(ln)]
    if hits:
        return daily, [f"{P.XROOTD_HOST}/{h}" for h in sorted(hits)]

    # 2. curated per-version area (sharded by thousands/hundreds)
    nn000 = f"{run // 1000 * 1000:08d}"
    nnn00 = f"{run // 100 * 100:08d}"
    for ver in P.RTRAW_CURATED_VERSIONS:
        d = f"{P.RTRAW_CURATED_BASE}/{ver}/global_trigger/{nn000}/{nnn00}/{run}"
        hits = [ln for ln in xrdfs_ls(d) if ln.endswith(".rtraw")]
        if hits:
            return d, [f"{P.XROOTD_HOST}/{h}" for h in sorted(hits)]

    raise SystemExit(f"[Error] no rtraw found for RUN {run} "
                     f"(tried {daily} and curated {P.RTRAW_CURATED_VERSIONS})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("run", type=int)
    ap.add_argument("--out", required=True, help="output list file (txt)")
    ap.add_argument("--slice", type=int, default=None,
                    help="keep only the first N files (default: all)")
    args = ap.parse_args()

    where, files = find_rtraw(args.run)
    if args.slice:
        files = files[: args.slice]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(u + "\n" for u in files))

    # the DAQ filename carries source/position, e.g.
    # RUN.10110.JUNODAQ.Calib-ACU-AmC117-Global-Pos-x0y0z0.ds-2...
    name = files[0].rsplit("/", 1)[-1] if files else ""
    m = re.search(r"JUNODAQ\.([^.]+)\.ds-", name)
    print(f"[Info] RUN {args.run}: {len(files)} rtraw file(s) from {where}")
    print(f"[Info] stream tag : {m.group(1) if m else '?'}")
    print(f"[Info] list file  : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
