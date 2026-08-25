#!/usr/bin/env python3
"""
convert_edm_to_npz.py
=====================
Stage 2: convert EDM ROOT files (CDCalib + Time trees) to a per-run NPZ.

Adapted from juno_calibration_acu_gamma_source/npz_from_root/
convert_root_to_npz.py (Shubing Liu, 2026-03-26). Differences:
  - input/output directories are local project paths (config/paths.py)
  - --input-dir can be overridden (e.g. the pre-existing ReProd26B EDM data
    on lustrefs, see config/paths.py: REMOTE_EDM_DIR)

Usage:
    python src/convert_edm_to_npz.py --run 12370
    python src/convert_edm_to_npz.py --run 12370 --input-dir /lustrefs/.../EDM_from_esd/Data
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

import numpy as np
import uproot

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from config.paths import EDM_DIR, NPZ_RAW_DIR, REMOTE_EDM_DIR  # noqa: E402

BRANCHES = [
    "global_time_s", "global_time_ns", "trigger_type",
    "MuonVeto", "totalPE", "omilrec_x", "omilrec_y", "omilrec_z", "omilrec_energy",
]


def get_chunk_sort_key(file_path: str):
    """Sort key by numeric chunk range in file name: run_<id>_<start>_<end>.root"""
    name = os.path.basename(file_path)
    match = re.search(r"run_(\d+)_(\d+)_(\d+)\.root$", name)
    if match:
        return int(match.group(2)), int(match.group(3))
    match_single = re.search(r"run_(\d+)\.root$", name)
    if match_single:
        return 0, 0
    return (10**9, 10**9)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--run", type=int, required=True, help="Run number")
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Directory with run_*.root files (default: local data/edm; "
             f"or the remote ReProd26B data at {REMOTE_EDM_DIR})",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help=f"Output directory (default: {NPZ_RAW_DIR})",
    )
    args = parser.parse_args()

    input_dir = args.input_dir or str(EDM_DIR)
    out_dir = args.out_dir or str(NPZ_RAW_DIR)
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isdir(input_dir):
        print(f"Input directory not found: {input_dir}")
        return 1

    file_groups: dict[str, list[str]] = defaultdict(list)
    for f in sorted(os.listdir(input_dir)):
        if not f.endswith(".root"):
            continue
        match = re.search(r"run_(\d+)", f)
        if not match or int(match.group(1)) != args.run:
            continue
        file_groups[match.group(1)].append(os.path.join(input_dir, f))

    if not file_groups:
        print(f"No EDM ROOT files found for RUN {args.run} in {input_dir}.")
        print("Hint: for pre-existing ReProd26B data use")
        print(f"    --input-dir {REMOTE_EDM_DIR}")
        return 1

    file_list = file_groups[str(args.run)]
    print(f"RUN {args.run}: {len(file_list)} EDM file(s) from {input_dir}")

    combined_data = {b: [] for b in BRANCHES}
    total_tltime = 0.0

    for file_path in sorted(file_list, key=get_chunk_sort_key):
        try:
            with uproot.open(file_path) as f:
                tree = f["CDCalib"]
                data = tree.arrays(BRANCHES, library="np")
                for b in BRANCHES:
                    combined_data[b].append(data[b])

                time_tree = f["Time"]
                keys = time_tree.keys()
                if "TLTime_s" in keys and "TLTime_ns" in keys:
                    tl_s = time_tree.arrays(["TLTime_s"], library="np")["TLTime_s"]
                    tl_ns = time_tree.arrays(["TLTime_ns"], library="np")["TLTime_ns"]
                    total_tltime += np.sum(tl_s) + np.sum(tl_ns) / 1e9
                elif "TLTime" in keys:
                    tl_times = time_tree.arrays(["TLTime"], library="np")["TLTime"]
                    total_tltime += np.sum(tl_times) / 1e9
                else:
                    print(f"Warning: no TLTime information in {file_path}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

    final_npz_data = {}
    for b in BRANCHES:
        final_npz_data[b] = (
            np.concatenate(combined_data[b]) if combined_data[b] else np.array([])
        )
    final_npz_data["LivingTime"] = total_tltime

    save_path = os.path.join(out_dir, f"RUN{args.run}.npz")
    np.savez(save_path, **final_npz_data)

    n_entries = (
        len(final_npz_data["global_time_s"])
        if len(final_npz_data["global_time_s"])
        else 0
    )
    print(f"-> Saved {save_path} (Entries: {n_entries}, LiveTime: {total_tltime:.2f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
