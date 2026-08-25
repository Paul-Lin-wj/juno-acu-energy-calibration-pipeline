#!/usr/bin/env python3
"""
list_esd.py
===========
Discover the ESD files of a calibration run on the JUNO EOS (xrootd) and
write a file list with xrootd URLs.

This replaces the cluster-only `eos ls` CLI: it uses the `xrdfs` client
tool shipped with the CVMFS JUNO offline software (see config/paths.py:
CVMFS_XROOTD_BIN).

Directory layout (standard ReProd26B global_trigger tree):

    {ESD_BASE}/{run_block:08d}/{sub_block:08d}_{CalibData_}{phase}_{tag}/{run_id}/
        RUN.{run_id}.JUNODAQ.Calib-ACU-<SRC>-...esd

where run_block = (run // 1000) * 1000 and sub_block = (run // 100) * 100.
Both the `*_CalibData_*` and the plain `*` sub-block directories are searched
(calib runs live in CalibData).

Usage:
    python src/list_esd.py 12370
    python src/list_esd.py 12370 --out my_esd_list.txt --max-files 5

Output: one xrootd URL per line (CERN EOS double-slash form), e.g.
    root://junoeos01.ihep.ac.cn//eos/juno/.../12370/RUN.12370...esd
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config.paths import (  # noqa: E402
    CVMFS_SETUP,
    CVMFS_XROOTD_BIN,
    ESD_BASE,
    XROOTD_HOST,
)


def _cvmfs_env() -> dict:
    """Capture the full environment after sourcing the CVMFS JUNO setup script
    (PATH, LD_LIBRARY_PATH, ...). Cached after the first call."""
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return _ENV_CACHE
    probe = (
        f"source {CVMFS_SETUP} >/dev/null 2>&1 && env"
    )
    result = subprocess.run(
        ["bash", "-c", probe], capture_output=True, text=True, timeout=120
    )
    env = dict(os.environ)
    for line in (result.stdout or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    if "xrdfs" not in env.get("PATH", ""):
        env["PATH"] = f"{CVMFS_XROOTD_BIN}:{env.get('PATH', '')}"
    _ENV_CACHE = env
    return env


_ENV_CACHE: dict | None = None


def _xrdfs_ls(path: str) -> list[str]:
    """List a directory on EOS via xrdfs. Returns entry names (no full paths)."""
    cmd = [
        "xrdfs",
        XROOTD_HOST,
        "ls",
        path,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, env=_cvmfs_env(), timeout=120
    )
    entries = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line or line.startswith("[ERROR]") or "Plugin" in line:
            continue
        # xrdfs prints either the full path or the bare name
        entries.append(line.rsplit("/", 1)[-1])
    return entries


def find_esd_run_dir(run_id: int, esd_base: str) -> str:
    """Locate the EOS directory containing the .esd files of *run_id*."""
    run_block = (run_id // 1000) * 1000
    sub_block = (run_id // 100) * 100
    prefix_dir = f"{run_block:08d}"
    sub_prefix = f"{sub_block:08d}"

    block_dir = f"{esd_base}/{prefix_dir}/"
    entries = _xrdfs_ls(block_dir)
    if not entries:
        raise FileNotFoundError(
            f"Block directory not found or empty: {block_dir}"
        )

    candidates = [
        e for e in entries if e.startswith(sub_prefix) and "_" in e
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No sub-block dir with prefix {sub_prefix} in {block_dir}"
        )

    # Prefer the CalibData sub-block (calibration runs), fall back to plain.
    candidates.sort(key=lambda e: (0 if "CalibData" in e else 1, e))

    for sub in candidates:
        run_dir = f"{block_dir}{sub}/{run_id}"
        try:
            files = _xrdfs_ls(run_dir)
        except Exception:
            continue
        esd_files = sorted(f for f in files if f.endswith(".esd"))
        if esd_files:
            return run_dir, esd_files
    raise FileNotFoundError(
        f"No .esd files found for run {run_id} under {block_dir}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("run", type=int, help="Run number, e.g. 12370")
    parser.add_argument(
        "--base",
        default=ESD_BASE,
        help=f"EOS base directory (default: {ESD_BASE})",
    )
    parser.add_argument("--out", default=None, help="Output file-list path")
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Keep only the first N files (for slice testing)",
    )
    args = parser.parse_args()

    run_dir, esd_files = find_esd_run_dir(args.run, args.base)
    print(f"ESD run directory : {run_dir}")
    print(f"ESD files         : {len(esd_files)}")

    # IHEP EOS gateway (CERN EOS convention) expects the double-slash URL form:
    #   root://host//eos/juno/...
    urls = [f"{XROOTD_HOST}/{run_dir}/{f}" for f in esd_files]
    if args.max_files is not None:
        urls = urls[: args.max_files]
        print(f"Kept first {len(urls)} files (--max-files).")

    out = args.out or f"esd_list_{args.run}.txt"
    with open(out, "w") as fh:
        fh.write("\n".join(urls) + "\n")
    print(f"File list written : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
