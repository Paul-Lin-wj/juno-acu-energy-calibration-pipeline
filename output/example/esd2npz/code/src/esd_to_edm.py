#!/usr/bin/env python3
"""
esd_to_edm.py
=============
Stage 1: reconstruct ESD files into EDM ROOT files (CDCalib + Time trees)
using the MySimpleTag algorithm from JUNOSW_MyAlgz.

This is the ONLY stage that needs the external JUNO offline environment:
  - CVMFS JUNO software  (CVMFS_SETUP in config/paths.py)
  - JUNOSW_MyAlgz build  (JUNOSW_SETUP / RUN_PY in config/paths.py)
  - xrootd access to EOS  (ESD files are read natively by the C++ code)

The ESD file list is produced by src/list_esd.py (xrootd URLs, one per line).

Usage:
    # full run (all ESD files, ~hours for 100+ files)
    python src/esd_to_edm.py 12370 --esd-list esd_list_12370.txt

    # slice of 5 ESD files (for a quick end-to-end test)
    python src/esd_to_edm.py 12370 --esd-list esd_list_12370.txt --start 0 --end 4

Output: data/edm/run_<RUN>_<start>_<end>.root
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config.paths import (  # noqa: E402
    CVMFS_SETUP,
    EDM_DIR,
    JUNOSW_SETUP,
    LIB_FALLBACK_DIRS,
    RUN_PY,
)


def build_wrapper_script(esd_list: str, start: int, end: int, out_root: str) -> str:
    """Write a bash wrapper that sources the environments and runs run.py."""
    return f"""#!/bin/bash
set -e
PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJ_DIR"
source {CVMFS_SETUP}
source {JUNOSW_SETUP}
# Hosts without libpcre.so.1 (newer distros): use the project-local copy in
# lib/ (fetched by setup_env.sh from {LIB_FALLBACK_DIRS[0]}).
if ! ldconfig -p 2>/dev/null | grep -q "libpcre.so.1"; then
    if [ ! -e "$PROJ_DIR/lib/libpcre.so.1" ]; then
        echo "ERROR: libpcre.so.1 missing; run 'bash setup_env.sh' first." >&2
        exit 1
    fi
    export LD_LIBRARY_PATH="$PROJ_DIR/lib:${{LD_LIBRARY_PATH:-}}"
fi
# slice the esd list: 0-based inclusive [start, end] -> 1-based sed range
sed -n "{start + 1},{end + 1}p" "{esd_list}" > "{tempfile.gettempdir()}/esd_slice_${{RUNNUM}}.txt"
n=$(wc -l < "{tempfile.gettempdir()}/esd_slice_${{RUNNUM}}.txt")
if [ "$n" -eq 0 ]; then echo "Empty slice"; exit 1; fi
echo "Reconstructing $n ESD files..."
python {RUN_PY} \\
    --evtmax -1 \\
    --loglevel Fatal \\
    --input-list "{tempfile.gettempdir()}/esd_slice_${{RUNNUM}}.txt" \\
    --user-output "{out_root}"
echo "Done: {out_root}"
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("run", type=int, help="Run number")
    parser.add_argument(
        "--esd-list",
        required=True,
        help="ESD file list (xrootd URLs, one per line; from src/list_esd.py)",
    )
    parser.add_argument("--start", type=int, default=0, help="First file index (0-based)")
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="Last file index (0-based, inclusive). Default: all files.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output ROOT file (default: data/edm/run_<RUN>_<start>_<end>.root)",
    )
    args = parser.parse_args()

    if not os.path.exists(CVMFS_SETUP):
        print(f"ERROR: CVMFS setup not found: {CVMFS_SETUP}")
        return 1
    if not os.path.exists(JUNOSW_SETUP):
        print(f"ERROR: JUNOSW setup not found: {JUNOSW_SETUP}")
        return 1
    if not os.path.exists(RUN_PY):
        print(f"ERROR: run.py not found: {RUN_PY}")
        return 1
    if not os.path.exists(args.esd_list):
        print(f"ERROR: ESD list not found: {args.esd_list}")
        return 1

    with open(args.esd_list) as f:
        total = sum(1 for line in f if line.strip())
    end = args.end if args.end is not None else total - 1
    if args.start < 0 or end >= total or args.start > end:
        print(f"ERROR: slice [{args.start},{end}] out of range (total {total})")
        return 1

    out_root = args.out or str(EDM_DIR / f"run_{args.run}_{args.start}_{end}.root")
    os.makedirs(os.path.dirname(out_root), exist_ok=True)
    if os.path.exists(out_root):
        print(f"Output already exists: {out_root} (delete it to re-run)")
        return 0

    wrapper = build_wrapper_script(args.esd_list, args.start, end, out_root)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".sh", delete=False, dir="."
    ) as fh:
        fh.write(wrapper)
        wrapper_path = fh.name
    os.chmod(wrapper_path, 0o755)

    os.environ["RUNNUM"] = str(args.run)
    print(f"ESD files : {end - args.start + 1} / {total}")
    print(f"Output    : {out_root}")
    print("Starting ESD->EDM reconstruction (this can take a while)...")
    t0 = time.time()
    result = subprocess.run(["bash", wrapper_path], env=dict(os.environ))
    os.unlink(wrapper_path)
    if result.returncode != 0:
        print(f"ERROR: reconstruction failed (exit {result.returncode})")
        return result.returncode
    print(f"Finished in {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
