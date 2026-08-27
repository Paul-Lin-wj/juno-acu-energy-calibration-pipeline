#!/usr/bin/env python3
"""
apply_final_correction.py
=========================
Stage 3: apply the full 26B energy correction (r-bias vertex, 2D spatial,
v2 time stability, phase absolute scale) to the raw OMILREC NPZ.

Adapted from juno_calibration_acu_gamma_source/Finalcorrection_from_npzESD/
apply_final_correction.py. The correction API (correction_api.py) and all
correction data were copied into this project under input/correction/, so
this stage is fully self-contained (numpy/pandas/scipy only).

Usage:
    python src/apply_final_correction.py 12370
    python src/apply_final_correction.py 12370 --input /path/RUN12370.npz
"""

import argparse
import os
import sys

import numpy as np

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BASE_DIR)
sys.path.insert(0, _BASE_DIR)
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "config"))

import paths  # noqa: E402

sys.path.insert(0, str(paths.CORRECTION_API_DIR))
from correction_api import EnergyCorrection26B  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply 26B Finalcorrection to a raw OMILREC NPZ"
    )
    parser.add_argument("run", type=int, help="Run number")
    parser.add_argument(
        "--input",
        default=None,
        help="Input RUN{run}.npz (default: data/npz_raw/RUN{run}.npz)",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help=f"Output directory (default: {paths.NPZ_CORRECTED_DIR})",
    )
    args = parser.parse_args()

    input_path = args.input or str(paths.NPZ_RAW_DIR / f"RUN{args.run}.npz")
    out_dir = args.out_dir or str(paths.NPZ_CORRECTED_DIR)
    output_path = os.path.join(out_dir, f"RUN{args.run}.npz")

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        print(f"Hint: run 'python src/convert_edm_to_npz.py --run {args.run}' first.")
        return 1

    os.makedirs(out_dir, exist_ok=True)

    corr = EnergyCorrection26B(data_dir=str(paths.CORRECTION_DATA_DIR))

    with np.load(input_path, allow_pickle=True) as d:
        event_time = (
            d["global_time_s"].astype(np.float64)
            + d["global_time_ns"].astype(np.float64) * 1e-9
        )
        energy = d["omilrec_energy"]
        x = d["omilrec_x"]
        y = d["omilrec_y"]
        z = d["omilrec_z"]

        x_corr, y_corr, z_corr = corr.correct_vertex_rbias(x, y, z, position_unit="mm")
        spatial = corr.spatial_factor_from_position(
            x_corr, y_corr, z_corr, run=args.run, position_unit="mm"
        )
        time_factor = corr.time_factor(event_time)
        phase = corr.phase_from_run(args.run)
        abs_scale = corr.absolute_scale_for_phase(phase)
        total_factor = spatial * abs_scale / time_factor
        energy_corr = np.asarray(energy, dtype=np.float64) * total_factor

        data_dict = {key: d[key] for key in d.files}
        data_dict["omilrec_energy"] = energy_corr.astype(d["omilrec_energy"].dtype)
        data_dict["omilrec_x"] = x_corr.astype(d["omilrec_x"].dtype)
        data_dict["omilrec_y"] = y_corr.astype(d["omilrec_y"].dtype)
        data_dict["omilrec_z"] = z_corr.astype(d["omilrec_z"].dtype)

    np.savez(output_path, **data_dict)

    n_events = len(event_time)
    print(f"[INFO] RUN{args.run}: phase={phase}, {n_events} events -> {output_path}")
    print(f"[INFO] absolute_scale={abs_scale:.8f}")
    print(f"[INFO] spatial_factor range: [{spatial.min():.6f}, {spatial.max():.6f}]")
    print(f"[INFO] time_factor range: [{time_factor.min():.6f}, {time_factor.max():.6f}]")
    print(f"[INFO] total_factor range: [{total_factor.min():.6f}, {total_factor.max():.6f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
