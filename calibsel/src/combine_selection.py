# -----------------------------------------------------------------------------
# Program: CombineSelection.py
# Author: Shubing Liu <liusb@ihep.ac.cn>
# Created: 2025-01-11
# Updated: 2026-01-17
# Description: 
#   Selects single event calibration sources based on spatial and energy cuts.
#   - Reads config to determine Source type and Background Run.
#   - Performs Fiducial Volume (EFV) cuts.
#   - Generates analysis plots.
#   - Saves results in NPZ (Spatial Cut only).
#   - Saves Timestamps in two versions:
#       1. Spatial Cut only (woEcut)
#       2. Spatial + Energy Cut (Ecut)
# -----------------------------------------------------------------------------

import argparse
import sys
import os

# --- Set backend to Agg before importing pyplot ---
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import math
import pandas as pd
from glob import glob
import datetime

# Local analysis utilities (inlined from the external reconstruction_ana
# package; see src/local_utils.py for the source attribution).
from local_utils import (  # noqa: E402
    GetBinCenter,
    HistBasedLimitFinding,
    save_arrays_to_text,
    get_memory_usage,
)

from collections import Counter

# --- Version Check Print ---
print("--- Running Updated Script (Dual Timestamp Output: woEcut & Ecut) ---")

# --- 1. Configuration & Inputs ---

# NOTE (standalone_esd2npz): adapted from juno_calibration_acu_gamma_source.
# All inputs/outputs now live inside this project; the only external
# dependency of this stage is the Python packages (numpy/pandas/matplotlib).

def _validate_ecorrection(value):
    if value is None:
        return None
    if not value.strip() or "/" in value or ".." in value:
        raise argparse.ArgumentTypeError(
            "Invalid --Ecorrection: must be a single path segment (e.g. Po214)"
        )
    return value.strip()


def resolve_selection_paths(datasource, ecorrection, finalcorrection, analysis_base, module_dir):
    # Local project layout:
    #   input  = data/npz_corrected   (output of stage 3, Finalcorrection)
    #   output = data/selection
    input_dir = f"{module_dir}/../data/npz_corrected"
    output_base = f"{module_dir}/../data/selection"
    return input_dir, output_base


_parser = argparse.ArgumentParser(description="Singles selection (standalone_esd2npz)")
_parser.add_argument("run", type=int, help="Calibration RUN number")
_parser.add_argument(
    "--datasource",
    type=str,
    choices=("esd", "miniesd"),
    default="esd",
    help="kept for CLI compatibility (paths are local now)",
)
_parser.add_argument(
    "--Ecorrection",
    type=_validate_ecorrection,
    default=None,
    help="kept for CLI compatibility (paths are local now)",
)
_parser.add_argument(
    "--Finalcorrection",
    action="store_true",
    help="kept for CLI compatibility (input is data/npz_corrected now)",
)
_parser.add_argument(
    "--input-dir",
    default=None,
    help="Override input NPZ directory (default: <project>/data/npz_corrected)",
)
_parser.add_argument(
    "--out-dir",
    default=None,
    help="Override output base directory (default: <project>/data/selection)",
)
_cli_args, _ = _parser.parse_known_args()
calib_run = _cli_args.run
_datasource = _cli_args.datasource
_ecorrection = _cli_args.Ecorrection
_finalcorrection = _cli_args.Finalcorrection

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_BASE_DIR = os.path.dirname(BASE_DIR)

INPUT_DATA_PATH, OUTPUT_BASE_DIR = resolve_selection_paths(
    _datasource, _ecorrection, _finalcorrection, ANALYSIS_BASE_DIR, BASE_DIR,
)
if _cli_args.input_dir is not None:
    INPUT_DATA_PATH = _cli_args.input_dir
if _cli_args.out_dir is not None:
    OUTPUT_BASE_DIR = _cli_args.out_dir
INPUT_DATA_PATH = os.path.normpath(INPUT_DATA_PATH)
OUTPUT_BASE_DIR = os.path.normpath(OUTPUT_BASE_DIR)
CALIB_INFO_FILE = f"{ANALYSIS_BASE_DIR}/calib_run_info/calib_to_analyze.txt"
CALIB_POS_FILE = f"{ANALYSIS_BASE_DIR}/calib_run_info/CalibRUN_from_file.csv"

# Output Directories
TIMESTAMP_DIR_WO_ECUT = f"{OUTPUT_BASE_DIR}/Timestamp_wo_Ecut"
TIMESTAMP_DIR_ECUT = f"{OUTPUT_BASE_DIR}/Timestamp_Ecut"

# Will be resolved from NPZ keys after loading run data.
vertex_chose = None
vertex_x = vertex_y = vertex_z = None
energy_key = None

dict_energy = {
    'Cs137': 0.662,
    'Mn54': 0.835,
    'Ge68': 1.022,
    'K40': 1.461,
    'nH': 2.223,
    'Co60': 2.506,
    'nC': 4.94,
    'O16': 6.13,
    'AmC': 2.223 
}

# Final fit window scales based on Step-1 energy region [best_region[0], best_region[1]].
FIT_LOW_SCALE = 0.9
FIT_HIGH_SCALE = 1.1
FIT_BIN_WIDTH = 0.002

# More robust initial ROI ranges for edge-source runs.
SOURCE_INITIAL_ROI_SCALE = {
    "Ge68": (0.45, 1.20),
}

# --- 2. Helper Functions ---

def get_run_config(target_run, config_file):
    """Parses config file for Source and PhysicsRun."""
    source_found = None
    bkg_run_found = None
    
    if not os.path.exists(config_file):
        print(f"Error: Config file not found at {config_file}")
        sys.exit(1)

    with open(config_file, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue 
        parts = line.split(',')
        if len(parts) < 2: continue
            
        src = parts[0].strip()
        run_range = parts[1].strip()
        
        try:
            if '-' in run_range:
                start_r, end_r = map(int, run_range.split('-'))
            else:
                start_r = int(run_range)
                end_r = int(run_range)
                
            if start_r <= target_run <= end_r:
                source_found = src
                if len(parts) >= 3:
                    try:
                        bkg_run_found = int(parts[2].strip())
                    except ValueError:
                        pass
                break
        except ValueError:
            continue
            
    return source_found, bkg_run_found


def apply_muon_veto(event_dict, run_tag):
    """Keep events that are NOT vetoed by MuonVeto."""
    if "MuonVeto" not in event_dict:
        print(f"Warning: {run_tag} has no MuonVeto key. Skip muon-veto filtering.")
        return event_dict

    veto_flag = np.asarray(event_dict["MuonVeto"]).astype(bool)
    pass_mask = ~veto_flag
    n_total = pass_mask.size
    n_pass = int(np.sum(pass_mask))

    filtered = {}
    for key, val in event_dict.items():
        arr = np.asarray(val)
        if arr.shape == (n_total,):
            filtered[key] = arr[pass_mask]
        else:
            filtered[key] = val

    print(f"{run_tag} MuonVeto(pass=not-vetoed): {n_pass}/{n_total} events kept ({(n_pass / max(n_total, 1)) * 100:.2f}%).")
    return filtered

def fit_quadratic_plus_gaussian_grid(x, y, yerr):
    """Weighted grid-search fit for: a*x^2 + b*x + c + A*exp(-(x-mu)^2/(2*sigma^2))."""
    mu_grid = np.linspace(np.min(x), np.max(x), 180)
    sigma_grid = np.linspace(0.005, 0.20, 160)

    best = None
    best_chi2 = np.inf

    inv_err = 1.0 / np.clip(yerr, 1e-12, None)
    x2 = x * x

    for mu in mu_grid:
        dx = x - mu
        for sigma in sigma_grid:
            g = np.exp(-0.5 * (dx / sigma) ** 2)
            design = np.column_stack([x2, x, np.ones_like(x), g])
            w_design = design * inv_err[:, None]
            w_y = y * inv_err

            try:
                coeffs, _, _, _ = np.linalg.lstsq(w_design, w_y, rcond=None)
            except np.linalg.LinAlgError:
                continue

            a, b, c, amp = coeffs
            if amp <= 0:
                continue

            y_fit = design @ coeffs
            chi2 = np.sum(((y - y_fit) / np.clip(yerr, 1e-12, None)) ** 2)
            if np.isfinite(chi2) and chi2 < best_chi2:
                best_chi2 = chi2
                best = {
                    "a": float(a), "b": float(b), "c": float(c), "amp": float(amp),
                    "mu": float(mu), "sigma": float(sigma), "chi2": float(chi2),
                }

    return best


def find_peak_region(x_values, y_values, source_name, default_region):
    """Find a robust peak-centered energy region from Rdiff curve."""
    x = np.asarray(x_values)
    y = np.nan_to_num(np.asarray(y_values), nan=0.0, posinf=0.0, neginf=0.0)
    if x.size < 8 or y.size != x.size:
        return default_region

    kernel = np.ones(5, dtype=float) / 5.0
    y_smooth = np.convolve(y, kernel, mode="same")
    peak_idx = int(np.argmax(y_smooth))
    peak_val = float(y_smooth[peak_idx])
    if not np.isfinite(peak_val) or peak_val <= 0:
        return default_region

    frac = 0.22 if source_name == "Ge68" else 0.30
    threshold = max(peak_val * frac, float(np.percentile(y_smooth, 60)))

    left = peak_idx
    right = peak_idx
    while left > 0 and y_smooth[left] >= threshold:
        left -= 1
    while right < (x.size - 1) and y_smooth[right] >= threshold:
        right += 1

    lo = float(x[max(left, 0)])
    hi = float(x[min(right, x.size - 1)])

    min_width = 0.18 if source_name == "Ge68" else 0.12
    if (hi - lo) < min_width:
        center = float(x[peak_idx])
        lo = center - 0.5 * min_width
        hi = center + 0.5 * min_width

    lo = max(float(default_region[0]), lo)
    hi = min(float(default_region[1]), hi)

    if not np.isfinite(lo) or not np.isfinite(hi) or lo >= hi:
        return default_region
    return [lo, hi]


# --- 3. Main Processing Logic ---

print(f"--- Processing Run {calib_run} ---")

# 3.1 Determine Source and BKG Run
found_source, found_bkg = get_run_config(calib_run, CALIB_INFO_FILE)

if found_source is None:
    print(f"Error: Run {calib_run} not found in config file {CALIB_INFO_FILE}")
    sys.exit(1)
    
calib_source = found_source

if found_bkg is not None:
    bkg_run = found_bkg
else:
    print(f"Error: Background Run NOT specified in config for Run {calib_run}.")
    sys.exit(1)

print(f"Configuration: Source={calib_source}, BkgRun={bkg_run}")

# 3.2 Prepare Directories
FIG_IMPORTANT_DIR = f"{OUTPUT_BASE_DIR}/figures_check_important_new"
FIG_IMPORTANT_ALT_DIR = FIG_IMPORTANT_DIR
FIG_CHECK_DIR = f"{OUTPUT_BASE_DIR}/figrues_check"
NPZ_DIR = f"{OUTPUT_BASE_DIR}/npz"

for d in [FIG_IMPORTANT_DIR, FIG_IMPORTANT_ALT_DIR, FIG_CHECK_DIR, NPZ_DIR, TIMESTAMP_DIR_WO_ECUT, TIMESTAMP_DIR_ECUT]:
    os.makedirs(d, exist_ok=True)

# 3.3 Load Position Info
if os.path.exists(CALIB_POS_FILE):
    try:
        df_all_run = pd.read_csv(CALIB_POS_FILE)
        row = df_all_run[df_all_run["RUN"] == calib_run]
        if not row.empty:
            calib_x = row["X[m]"].values[0]
            calib_y = row["Y[m]"].values[0]
            calib_z = row["Z[m]"].values[0]
            source_date = row["Date"].values[0]
        else:
            print(f"Warning: Run {calib_run} not in position file. Using (0,0,0).")
            calib_x, calib_y, calib_z = 0., 0., 0.
            source_date = "Unknown"
    except Exception as e:
        print(f"Warning reading position file: {e}. Using (0,0,0).")
        calib_x, calib_y, calib_z = 0., 0., 0.
        source_date = "Unknown"
else:
    print("Warning: Position file not found. Using (0,0,0).")
    calib_x, calib_y, calib_z = 0., 0., 0.
    source_date = "Unknown"

calib_r = np.sqrt(calib_x**2 + calib_y**2 + calib_z**2)

# 3.4 Load NPZ Data
def load_npz(run):
    path = f"{INPUT_DATA_PATH}/RUN{run}.npz"
    if not os.path.exists(path):
        print(f"Error: Data file {path} not found.")
        sys.exit(1)

    # Avoid forcing object arrays (e.g. trigger_type) when allow_pickle=False.
    loaded = {}
    with np.load(path, allow_pickle=False) as npz:
        for key in npz.files:
            try:
                loaded[key] = npz[key]
            except ValueError:
                print(f"Warning: Skip object-like key {key} in {os.path.basename(path)}")
    return loaded

def resolve_reco_keys(npz_dict):
    candidates = [
        ("omilrec", "omilrec_x", "omilrec_y", "omilrec_z", "omilrec_energy"),
        ("oec", "oec_x", "oec_y", "oec_z", "oec_energy"),
    ]
    for name, x_key, y_key, z_key, e_key in candidates:
        if all(k in npz_dict for k in [x_key, y_key, z_key, e_key]):
            return name, x_key, y_key, z_key, e_key
    raise KeyError(f"No supported reco key set found in NPZ keys: {sorted(npz_dict.keys())}")


dict_calib = load_npz(calib_run)
dict_bkg = load_npz(bkg_run)

dict_calib = apply_muon_veto(dict_calib, f"Calib RUN{calib_run}")
dict_bkg = apply_muon_veto(dict_bkg, f"Bkg RUN{bkg_run}")

vertex_chose, vertex_x, vertex_y, vertex_z, energy_key = resolve_reco_keys(dict_calib)
missing_in_bkg = [k for k in [vertex_x, vertex_y, vertex_z, energy_key] if k not in dict_bkg]
if missing_in_bkg:
    print(f"Error: Background NPZ missing required keys: {missing_in_bkg}")
    sys.exit(1)

dict_calib["rho"] = np.sqrt(dict_calib[vertex_x]**2 + dict_calib[vertex_y]**2)
dict_bkg["rho"] = np.sqrt(dict_bkg[vertex_x]**2 + dict_bkg[vertex_y]**2)
print(f"Using reconstruction keys: {energy_key}, {vertex_x}/{vertex_y}/{vertex_z}")

get_memory_usage()

print(f"Calib Run ({calib_source}) {calib_run}: {len(dict_calib['global_time_s'])} evts, {dict_calib['LivingTime']:.2f} s")
print(f"Bkg Run {bkg_run}: {len(dict_bkg['global_time_s'])} evts, {dict_bkg['LivingTime']:.2f} s")

source_energy = dict_energy.get(calib_source, 1.0)
roi_scale = SOURCE_INITIAL_ROI_SCALE.get(calib_source, (0.6, 1.2))
energy_region = [source_energy * roi_scale[0], source_energy * roi_scale[1]]
print(f"ROI: [{energy_region[0]:.2f}, {energy_region[1]:.2f}] MeV")

# --- 4. Selection & Plotting ---

# Plot 1: Energy Spectrum
bins_energy = np.arange(energy_region[0], energy_region[1], 0.005)

plt.figure(dpi=300, figsize=(5, 2.5))
Energy_rec = dict_calib[energy_key]
time_weights = np.ones_like(dict_calib[energy_key]) / dict_calib["LivingTime"]
CD_evt_rate = len(dict_calib[energy_key]) / dict_calib["LivingTime"]

plt.hist(
    Energy_rec, bins=bins_energy, weights=time_weights,
    histtype="step", color="tab:red",
    label=f"RUN{calib_run}: ({calib_x:.2f}, {calib_y:.2f}, {calib_z:.2f}) m {CD_evt_rate:.0f} Hz",
)
plt.hist(
    dict_bkg[energy_key], bins=bins_energy,
    weights=np.ones_like(dict_bkg[energy_key]) / dict_bkg["LivingTime"],
    alpha =0.3, color="tab:blue",
    label=f"BKG (RUN{bkg_run})\n{len(dict_bkg[energy_key]) / dict_bkg['LivingTime']:.1f} Hz",
)
plt.xlabel(f"Energy [MeV] (from OEC)")
plt.ylabel("Event Rate [Hz]")
plt.title(f"{calib_source} Calibration Energy Spectrum on {source_date}\nRun {calib_run} at R={calib_r:.2f} m")
plt.yscale("log")
plt.legend(fontsize=8)
plt.tight_layout()
try:
    plt.savefig(f"{FIG_CHECK_DIR}/Run{calib_run}_EnergySpectrum.png", bbox_inches="tight", pad_inches=0.05)
except: pass
plt.close()

# Plot 2: Rho vs Z
fig, axs = plt.subplots(figsize=(3, 4), dpi=300)
index_energy = (dict_calib[energy_key] > energy_region[0]) & (dict_calib[energy_key] < energy_region[1])
hist = axs.hist2d(
   dict_calib["rho"][index_energy] / 1e3,
   dict_calib[vertex_z][index_energy] / 1e3,
    bins=(100, 100),
    cmap="rainbow",
    norm="log",
)
axs.set_xlabel("$\\rho$ [m]")
axs.set_ylabel("Z [m]", labelpad=0.1)
axs.set_title(f"$\\rho$ VS. Z (from {vertex_chose} {calib_z:.1f} m)\n({calib_source} [{energy_region[0]:.1f}$~${energy_region[1]:.1f}] MeV)", x=0.5, fontsize=8)
axs.axhline(calib_z, color="tab:red", linestyle="--", linewidth=1)
plt.tight_layout()
try:
    plt.savefig(f"{FIG_CHECK_DIR}/Run{calib_run}_Rho_vs_Z.png")
except: pass
plt.close()

# Plot 3: Selection Process
rho_limit = 1

bins_rho = np.arange(0, 17, 0.1)
bins_rho_center = GetBinCenter(bins_rho)
bins_z = np.arange(-17.8, 17.8, 0.001)
bins_z_center = GetBinCenter(bins_z)
bins_z_Z_true = np.arange(0, 5, 0.001)
bins_z_Z_true_center = GetBinCenter(bins_z_Z_true)
bins_energy = np.arange(energy_region[0], energy_region[1], 0.01)
bins_energy_center = GetBinCenter(bins_energy)
RD_threshold = 0.1

BKG_living_time = dict_bkg["LivingTime"]
weights_bkg = np.ones_like(dict_bkg[energy_key]) / BKG_living_time
run_living_time = dict_calib["LivingTime"]
weights_run = np.ones_like(dict_calib[energy_key]) / run_living_time

fig, axes = plt.subplots(3, 2, figsize=(3 * 2.5, 2.5 * 3), dpi=300, width_ratios=[1, 2])
ax = axes[0, :]

# -- Step 1: Energy Region --
try:
    hist_run, _, _ = ax[0].hist(
        dict_calib[energy_key], bins=bins_energy, histtype="step", color="tab:red", weights=weights_run,
    )
    hist__bkg, _, _ = ax[0].hist(
        dict_bkg[energy_key], bins=bins_energy, alpha=0.3, color="tab:blue", weights=weights_bkg,
    )
    hist_diff = (hist_run - hist__bkg)*100
    with np.errstate(divide='ignore', invalid='ignore'):
        hist_diff_err = (hist__bkg / hist_run) * np.sqrt(
            1 / (hist_run * run_living_time) + 1 / (hist__bkg * BKG_living_time)
        )
    hist_diff_err = np.nan_to_num(hist_diff_err, posinf=0.0, neginf=0.0)

    ax[0].set_xlabel(f"$E_{{rec}}$ [MeV]")
    ax[0].set_ylabel("Event Rate [Hz]")
    ax[0].set_yscale("log")

    ax[1].errorbar(bins_energy_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
    RD_threshold = np.nanmean(hist_diff)
    scan_result = HistBasedLimitFinding(
        x_values=bins_energy_center, y_values=hist_diff, threshold=RD_threshold, direction="both", start_point=None,
    )
    start_point = scan_result[0]
    best_region_scan = scan_result[1:]
    best_region_peak = find_peak_region(
        x_values=bins_energy_center, y_values=hist_diff, source_name=calib_source, default_region=energy_region,
    )

    best_region = best_region_peak
    if (best_region_scan is not None and len(best_region_scan) == 2 and np.all(np.isfinite(best_region_scan))):
        best_region = [
            max(energy_region[0], min(best_region_peak[0], best_region_scan[0])),
            min(energy_region[1], max(best_region_peak[1], best_region_scan[1])),
        ]

    if not (len(best_region) == 2 and np.all(np.isfinite(best_region)) and best_region[0] < best_region[1]):
        best_region = energy_region

    print(f"Step1 Energy Region (robust): [{best_region[0]:.3f}, {best_region[1]:.3f}] MeV")

    try:
        if start_point is not None and np.isfinite(start_point):
            ax[1].axvline(start_point, ls = "--", color = "tab:green", label = f"Expected: {start_point:.1f} MeV")
    except: pass
        
    try:
        if np.isfinite(RD_threshold):
            ax[1].axhline(RD_threshold, ls = "--", color = "tab:red", label = f"R$_{{\\mathrm{{diff}}}}$ = {RD_threshold:.0f} %", zorder = 10, lw = 2)
    except: pass

    try:
        if best_region is not None and len(best_region) == 2 and np.all(np.isfinite(best_region)):
            ax[1].axvspan(best_region[0], best_region[1], color="tab:blue", alpha=0.3, label = f"Selected Region\n{best_region[0]:.2f} - {best_region[1]:.2f} MeV")
    except: pass

    ax[1].set_xlabel("$E_{{rec}}$ [MeV]")
    ax[1].set_ylabel("R$_{\\mathrm{diff}}$ [%]")
    try:
        if len(hist_diff) > 0:
            max_val = np.nanmax(hist_diff)
            if np.isfinite(max_val):
                ax[1].set_ylim(-10, max_val+10)
    except: pass
    if ax[1].get_legend_handles_labels()[0]:
        ax[1].legend(fontsize=8, framealpha=0.6)
except Exception as e:
    print(f"Warning: Step 1 Energy Plot Failed: {e}")
    if 'best_region' not in locals() or best_region is None:
        best_region = energy_region
    if 'start_point' not in locals():
        start_point = 0

# -- Step 2: Rho Limit --
ax = axes[1, :]
try:
    index_energy_run = (dict_calib[energy_key] > best_region[0]) & (dict_calib[energy_key] < best_region[1])
    index_energy_bkg = (dict_bkg[energy_key] > best_region[0]) & (dict_bkg[energy_key] < best_region[1])

    hist_run, _, _ = ax[0].hist(
        dict_calib["rho"][index_energy_run]/1e3, bins=bins_rho, histtype="step", color="tab:red", weights=weights_run[index_energy_run],
    )
    hist__bkg, _, _ = ax[0].hist(
        dict_bkg["rho"][index_energy_bkg]/1e3, bins=bins_rho, alpha=0.3, color="tab:blue", weights=weights_bkg[index_energy_bkg],
    )
    hist_diff = (hist_run - hist__bkg)*100
    with np.errstate(divide='ignore', invalid='ignore'):
        hist_diff_err = (hist__bkg / hist_run) * np.sqrt(
            1 / (hist_run * run_living_time) + 1 / (hist__bkg * BKG_living_time)
        )
    hist_diff_err = np.nan_to_num(hist_diff_err, posinf=0.0, neginf=0.0)

    ax[0].set_xlabel(f"$\\rho$ ($E_{{rec}}$ [m] in [{best_region[0]:.1f}, {best_region[1]:.1f}] MeV)")
    ax[0].set_yscale("log")

    ax[1].errorbar(bins_rho_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
    RD_threshold_rho = np.nanmean(hist_diff)
    scan_result = HistBasedLimitFinding(
        x_values=bins_rho_center, y_values=hist_diff, threshold=RD_threshold_rho, direction="right", start_point=0,
    )
    start_point = scan_result[0]
    rho_limit = scan_result[1]

    try:
        if np.isfinite(RD_threshold_rho):
            ax[1].axhline(RD_threshold_rho, ls = "--", color = "tab:red", label = f"R$_{{\\mathrm{{diff}}}}$ = {RD_threshold_rho:.0f} %", zorder = 10, lw = 2)
    except: pass

    try:
        if np.isfinite(rho_limit):
            ax[1].axvspan(0, rho_limit, color="tab:blue", alpha=0.3, label = f"Selected Region\n0 - {rho_limit:.2f} m")
    except: pass

    ax[1].set_xlabel("$\\rho$ [m]")
    ax[1].set_ylabel("R$_{\\mathrm{diff}}$ [%]")
    try:
        if len(hist_diff) > 0:
            max_val = np.nanmax(hist_diff)
            if np.isfinite(max_val):
                ax[1].set_ylim(-10, max_val+10)
    except: pass
    if ax[1].get_legend_handles_labels()[0]:
        ax[1].legend(fontsize=8, framealpha=0.6)
except Exception as e:
    print(f"Warning: Step 2 Rho Plot Failed: {e}")
    if 'rho_limit' not in locals():
        rho_limit = 1

# -- Step 3: Z Limit --
ax = axes[2, :]
try:
    index_rho_run = dict_calib["rho"]/1e3 <= rho_limit
    index_rho_bkg = dict_bkg["rho"]/1e3 <= rho_limit
    
    hist_run_tmp, _ = np.histogram(
        dict_calib[vertex_z][index_energy_run & index_rho_run]/1e3, bins=bins_z, weights=weights_run[index_energy_run & index_rho_run],
    )

    if np.abs(calib_z) >= 17.7: 
        index_z_tmp = np.logical_and(bins_z_center > (calib_z - 5), bins_z_center < (calib_z + 5))
        if np.any(index_z_tmp):
            z_expected = bins_z_center[index_z_tmp][np.argmax(hist_run_tmp[index_z_tmp])]
        else:
            z_expected = calib_z
    elif np.abs(calib_z) > 17: 
        z_expected = calib_z
    else:
        index_z_tmp = np.logical_and(bins_z_center > (calib_z - 0.5), bins_z_center < (calib_z + 0.5))
        if np.any(index_z_tmp):
            z_expected = bins_z_center[index_z_tmp][np.argmax(hist_run_tmp[index_z_tmp])]
        else:
            z_expected = calib_z
        
    hist_run, _, _ = ax[0].hist(
        np.abs(dict_calib[vertex_z][index_energy_run & index_rho_run]/1e3 - z_expected),
        bins=bins_z_Z_true, histtype="step", color="tab:red", weights=weights_run[index_energy_run & index_rho_run],
        label = f"True Z: {calib_z:.2f} m\nRec. Z: {z_expected:.2f} m",
    )
    hist__bkg, _, _ = ax[0].hist(
        np.abs(dict_bkg[vertex_z][index_energy_bkg & index_rho_bkg]/1e3 - z_expected),
        bins=bins_z_Z_true, alpha=0.3, color="tab:blue", weights=weights_bkg[index_energy_bkg & index_rho_bkg],
    )
    hist_diff = (hist_run - hist__bkg)*100
    with np.errstate(divide='ignore', invalid='ignore'):
        hist_diff_err = (hist__bkg / hist_run) * np.sqrt(
            1 / (hist_run * run_living_time) + 1 / (hist__bkg * BKG_living_time)
        )
    hist_diff_err = np.nan_to_num(hist_diff_err, posinf=0.0, neginf=0.0)

    ax[0].set_xlabel(f"Z [m]")
    ax[0].set_yscale("log")
    ax[0].legend(fontsize=8, framealpha=0.6)

    ax[1].errorbar(bins_z_Z_true_center, hist_diff, yerr=hist_diff_err, color="tab:orange", capsize=3, marker="o", mfc="None", markersize=2)
    
    if len(hist_diff) > 0:
        RD_threshold_z = np.nanmean(hist_diff)
    else:
        RD_threshold_z = 0
        
    # Original scan to find first crossing
    scan_result = HistBasedLimitFinding(
        x_values=bins_z_Z_true_center, y_values=hist_diff, threshold=RD_threshold_z, direction="right", start_point=None,
    )
    start_point = scan_result[0]
    z_limit_first = scan_result[1]
    
    # Robust check: from z_limit_first, look ahead 5 bins to confirm the crossing
    # If >=3 out of 5 points are below threshold, accept this as the boundary
    z_limit = z_limit_first
    if np.isfinite(z_limit_first):
        idx_first = np.argmin(np.abs(bins_z_Z_true_center - z_limit_first))
        if idx_first + 5 < len(bins_z_Z_true_center):
            # Check 5 points ahead starting from idx_first
            upcoming_5_indices = np.arange(idx_first, min(idx_first + 6, len(bins_z_Z_true_center)))
            upcoming_5_values = hist_diff[upcoming_5_indices]
            n_below = np.sum(upcoming_5_values < RD_threshold_z)
            print(f"Step3 Z-cut robust check: at z={z_limit_first:.4f}m, next 5 points: {n_below}/5 below threshold")
            if n_below >= 3:
                # Majority confirms: use this crossing
                z_limit = z_limit_first
            else:
                # Not enough points below, continue scanning to find next crossing
                for idx in range(idx_first + 1, len(bins_z_Z_true_center) - 5):
                    window = hist_diff[idx:idx+6]
                    if np.sum(window < RD_threshold_z) >= 3:
                        z_limit = float(bins_z_Z_true_center[idx])
                        print(f"Step3 Z-cut: found robust crossing at z={z_limit:.4f}m")
                        break
    
    print(f"Step3 Z-cut: RD_threshold={RD_threshold_z:.2f}%, z_limit={z_limit:.4f} m")
    
    if np.isfinite(z_limit) and z_limit < 1:
        z_limit = z_limit
    else:
        z_limit = 1.0

    try:
        if np.isfinite(RD_threshold_z):
            ax[1].axhline(RD_threshold_z, ls = "--", color = "tab:red", label = f"R$_{{\\mathrm{{diff}}}}$ = {RD_threshold_z:.0f} %", zorder = 10, lw = 2)
    except: pass

    try:
        if np.isfinite(z_limit):
            ax[1].axvspan(0, z_limit, color="tab:blue", alpha=0.3, label = f"Selected Region\n0 - {z_limit:.2f} m")
    except: pass

    ax[1].set_xlabel(r"$Z \ - \ Z_{{\mu}}$ [m]")
    ax[1].set_ylabel("R$_{\\mathrm{diff}}$ [%]")
    try:
        if len(hist_diff) > 0:
            max_val = np.nanmax(hist_diff)
            if np.isfinite(max_val):
                ax[1].set_ylim(-10, max_val+10)
    except: pass
    
    if ax[1].get_legend_handles_labels()[0]:
        ax[1].legend(fontsize=8, framealpha=0.6)

    print(f"z_expected: {z_expected:.3f} m; True: {calib_z:.3f} m \n")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Warning: Step 3 Z Plot Failed: {e}")
    if 'z_expected' not in locals():
        z_expected = calib_z
    if 'z_limit' not in locals():
        z_limit = 1.0

plt.suptitle(f"RUN{calib_run}({calib_source}): ({calib_x:.2f}, {calib_y:.2f}, {calib_z:.2f})", y = 0.97)
plt.tight_layout()
try:
    plt.savefig(f"{FIG_IMPORTANT_ALT_DIR}/Run{calib_run}_1_SelectionPlot.png")
except: pass
plt.close()

# --- 5. Saving Results ---

rho_scale = (dict_calib["rho"]/1e3/rho_limit)**2
z_scale= (dict_calib[vertex_z]/1e3 - z_expected)**2 /z_limit**2
index_ellipse = np.sqrt(rho_scale + z_scale) <= 1
index_EFV = index_ellipse

print(f"RUN{calib_run}: EFV event number: {np.sum(index_EFV)}/{len(index_EFV)}")
sys.stdout.flush()

rho_scale = (dict_bkg["rho"]/1e3/rho_limit)**2
z_scale= (dict_bkg[vertex_z]/1e3 - z_expected)**2 /z_limit**2
index_bkg_EFV = np.sqrt(rho_scale + z_scale) <= 1

# Plot 4: EFV Rho vs Z
print("Plotting EFV distribution...")
sys.stdout.flush()
try:
    fig, axs = plt.subplots(figsize=(3, 4), dpi=300)
    hist = axs.hist2d(
       dict_calib["rho"][index_EFV] / 1e3,
       dict_calib[vertex_z][index_EFV] / 1e3,
        bins=(np.arange(0, 17.7, 0.01), np.arange(-17.8, 17.8, 0.01)),
        cmap="rainbow",
        norm="log",
    )
    axs.set_xlabel("$\\rho$ [m]")
    axs.set_ylabel("Z [m]", labelpad=0.1)
    axs.set_title(f"$\\rho$ VS. Z (EFV)\n({calib_source} [{energy_region[0]:.1f}$~${energy_region[1]:.1f}] MeV)", x=0.5, fontsize=8)
    axs.axhline(calib_z, color="tab:red", linestyle="--", linewidth=1)
    plt.tight_layout()
    try:
        plt.savefig(f"{FIG_CHECK_DIR}/Run{calib_run}_Rho_vs_Z_EFV.png")
    except: pass
    plt.close()
except Exception as e:
    print(f"Warning: EFV Plot Failed: {e}")

print("Saving results (NPZ)...")
sys.stdout.flush()

calib_indices_int = np.nonzero(index_EFV)[0]

dict_save = {
    "calib_index": calib_indices_int,
    f"calib_{energy_key}": dict_calib[energy_key][index_EFV],
    f"calib_{vertex_x}": dict_calib[vertex_x][index_EFV],
    f"calib_{vertex_y}": dict_calib[vertex_y][index_EFV],
    f"calib_{vertex_z}": dict_calib[vertex_z][index_EFV],
}
np.savez(f"{NPZ_DIR}/Run{calib_run}_SelectionResult.npz", **dict_save)

# Plot 5: Final Spectrum
print("Plotting final spectrum...")
sys.stdout.flush()
try:
    plt.figure(figsize=(6, 2))
    bins_energy = np.arange(0.0, 6, 0.01)
    bins_energy_center = GetBinCenter(bins_energy)

    plt.hist(
        dict_calib[energy_key], bins=bins_energy, histtype="step", color="tab:orange",
        label="After Muon Veto", weights=np.ones_like(dict_calib[energy_key]) / dict_calib["LivingTime"],
    )
    hist_run, _, _ = plt.hist(
        dict_calib[energy_key][index_EFV], bins=bins_energy, histtype="step", color="tab:green",
        label="After FV Cut", weights=np.ones(np.sum(index_EFV)) / dict_calib["LivingTime"],
    )
    hist_count_BKG, _, _ = plt.hist(
        dict_bkg[energy_key][index_bkg_EFV], bins=bins_energy,
        weights=np.ones_like(dict_bkg[energy_key][index_bkg_EFV]) / dict_bkg["LivingTime"],
        label="BKG (by Physic Run)", alpha=0.3, color="tab:blue",
    )
    hist_diff = hist_run - hist_count_BKG
    plt.hist(
        bins_energy_center, bins=bins_energy, weights=hist_diff,
        alpha=0.3, color="tab:red", label="After BKG substracted", linestyle="--",
    )
    plt.xlabel("Rec Energy [MeV]", fontsize=13)
    plt.ylabel("Event Rate [Hz]", fontsize=13)
    plt.title(f"{calib_source} (RUN {calib_run}: ({calib_x:.2f}, {calib_y:.2f}, {calib_z:.2f}))", fontsize=10)
    plt.yscale("log")
    plt.legend(fontsize=8, framealpha=0.6, ncol=1, loc="upper right")
    plt.tight_layout()
    try:
        plt.savefig(f"{FIG_CHECK_DIR}/Run{calib_run}_EnergySpectrum_Selection.png")
    except: pass
    plt.close()
except Exception as e:
    print(f"Warning: Final Spectrum Plot Failed: {e}")


# Plot 6: FV spectrum fit (quadratic background + Gaussian signal)
fit_energy_region = None
try:
    fit_min = best_region[0] * FIT_LOW_SCALE
    fit_max = best_region[1] * FIT_HIGH_SCALE
    fit_energy_region = [fit_min, fit_max]

    energy_fv = dict_calib[energy_key][index_EFV]

    # Define plot range first, then bin over the full displayed range.
    plot_xmin = 0.9 * fit_min
    plot_xmax = 1.1 * fit_max
    plot_bins = np.arange(plot_xmin, plot_xmax + FIT_BIN_WIDTH, FIT_BIN_WIDTH)
    if len(plot_bins) < 3:
        raise RuntimeError("Invalid plot bins.")

    hist_counts, _ = np.histogram(energy_fv, bins=plot_bins)
    x_center = GetBinCenter(plot_bins)
    fit_bin_width = float(np.median(np.diff(plot_bins)))
    y_entries = hist_counts.astype(float)
    y_err = np.sqrt(np.maximum(hist_counts, 1.0))
    x_err = np.full_like(x_center, fit_bin_width * 0.5, dtype=float)

    fit_mask = (x_center >= fit_min) & (x_center <= fit_max) & (hist_counts > 0)
    if np.sum(fit_mask) < 8:
        raise RuntimeError("Not enough bins with events for fit.")

    fit_result = fit_quadratic_plus_gaussian_grid(
        x=x_center[fit_mask],
        y=y_entries[fit_mask],
        yerr=y_err[fit_mask],
    )
    if fit_result is None:
        raise RuntimeError("Fit failed in grid search.")

    mu_fit = fit_result["mu"]
    sigma_fit = fit_result["sigma"]
    final_energy_region = [mu_fit - 3.0 * sigma_fit, mu_fit + 3.0 * sigma_fit]
    n_before_cut = int(energy_fv.size)
    n_after_cut = int(np.sum((energy_fv >= final_energy_region[0]) & (energy_fv <= final_energy_region[1])))
    cut_ratio = (1.0 - n_after_cut / max(n_before_cut, 1)) * 100.0
    n_fit_bins = int(np.sum(fit_mask))
    ndf = max(n_fit_bins - 6, 1)
    chi2_ndf = fit_result["chi2"] / ndf

    x_line = np.linspace(fit_min, fit_max, 1000)
    bkg_line = fit_result["a"] * x_line**2 + fit_result["b"] * x_line + fit_result["c"]
    gaus_line = fit_result["amp"] * np.exp(-0.5 * ((x_line - mu_fit) / sigma_fit) ** 2)
    total_line = bkg_line + gaus_line

    fig, ax = plt.subplots(figsize=(8.8, 4.0), dpi=300)
    ax.errorbar(
        x_center, y_entries, xerr=x_err, yerr=y_err,
        fmt="o", color="black", ecolor="black", elinewidth=0.8,
        markersize=2.5, capsize=1.5, label="Data (FV-selected)",
    )
    ax.plot(x_line, total_line, color="black", lw=1.5, label="Total fit")
    ax.plot(x_line, gaus_line, color="red", ls="--", lw=1.5, label="Gaussian")
    ax.plot(x_line, bkg_line, color="blue", ls="--", lw=1.5, label="Quadratic background")
    ax.axvline(fit_min, color="gray", ls="--", lw=1.0, label=f"Fit range: [{fit_min:.5f}, {fit_max:.5f}] MeV")
    ax.axvline(fit_max, color="gray", ls="--", lw=1.0)
    ax.axvline(final_energy_region[0], color="red", ls="--", lw=1.0, label=f"3$\\sigma$ cut: [{final_energy_region[0]:.5f}, {final_energy_region[1]:.5f}] MeV")
    ax.axvline(final_energy_region[1], color="red", ls="--", lw=1.0)
    ax.set_xlim(plot_xmin, plot_xmax)
    ax.set_xlabel("Energy [MeV]")
    ax.set_ylabel(f"Entries/{fit_bin_width:g} MeV")
    ax.set_title(f"RUN{calib_run} FV Spectrum Fit ({calib_source})\nPos=({calib_x:.2f}, {calib_y:.2f}, {calib_z:.2f}) m")

    stat_text = (
        f"$\\mu$ = {mu_fit:.5f} MeV\n"
        f"$\\sigma$ = {sigma_fit:.5f} MeV\n"
        f"$\\chi^2/ndf$ = {fit_result['chi2']:.2f}/{ndf:d} = {chi2_ndf:.3f}\n"
        f"Before cut: {n_before_cut:d}\n"
        f"After cut: {n_after_cut:d}\n"
        f"Cut fraction: {cut_ratio:.2f}%"
    )
    ax.text(1.02, 0.40, stat_text, transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.85))
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.00), fontsize=8, framealpha=0.85)
    fig.subplots_adjust(right=0.67)

    fit_plot_path = f"{FIG_IMPORTANT_DIR}/Run{calib_run}_2_EnergySpectrum_Fit.png"
    plt.savefig(fit_plot_path, bbox_inches="tight", pad_inches=0.05)
    plt.close()

    print(f"Saved fit plot to: {fit_plot_path}")
    print(f"Final Energy Cut (mu±3sigma): [{final_energy_region[0]:.5f}, {final_energy_region[1]:.5f}] MeV")
except Exception as e:
    print(f"Warning: FV spectrum fit failed: {e}")
    final_energy_region = None

# --- [MODIFIED] Saving Timestamps (Dual Output) ---
print("Saving timestamps...")
sys.stdout.flush()

# 1. Output Timestamp_wo_Ecut (Spatial Cut Only - Same as original logic)
try:
    TS_sec = dict_calib["global_time_s"][index_EFV]
    TS_nansec = dict_calib["global_time_ns"][index_EFV]
    timestamp_file_wo = f"{TIMESTAMP_DIR_WO_ECUT}/RUN{calib_run}.txt"

    try:
        save_arrays_to_text(TS_sec, TS_nansec, output_file=timestamp_file_wo)
    except NameError:
        with open(timestamp_file_wo, 'w') as f:
            for s, ns in zip(TS_sec, TS_nansec):
                f.write(f"{s} {ns}\n")
    print(f"Saved woEcut timestamp to: {timestamp_file_wo}")
except Exception as e:
    print(f"Error saving woEcut timestamp: {e}")


# 2. Output Timestamp_Ecut (Spatial Cut + Energy Cut)
try:
    # Ensure best_region is available (fallback to wide region if Step 1 failed)
    if 'best_region' not in locals() or best_region is None:
        best_region = energy_region

    # Apply final energy cut on top of spatial cut.
    # Preferred: FV-fit mean±3sigma; fallback: Step-1 best_region.
    if final_energy_region is not None:
        e_low, e_high = final_energy_region
    else:
        e_low, e_high = best_region

    index_energy_final = (dict_calib[energy_key] >= e_low) & (dict_calib[energy_key] <= e_high)
    index_combined = index_EFV & index_energy_final
    
    TS_sec_E = dict_calib["global_time_s"][index_combined]
    TS_nansec_E = dict_calib["global_time_ns"][index_combined]
    timestamp_file_E = f"{TIMESTAMP_DIR_ECUT}/RUN{calib_run}.txt"

    try:
        save_arrays_to_text(TS_sec_E, TS_nansec_E, output_file=timestamp_file_E)
    except NameError:
        with open(timestamp_file_E, 'w') as f:
            for s, ns in zip(TS_sec_E, TS_nansec_E):
                f.write(f"{s} {ns}\n")
    print(f"Saved Ecut timestamp ({e_low:.5f}-{e_high:.5f} MeV) to: {timestamp_file_E}")
    print(f"Events after Ecut: {np.sum(index_combined)}")

except Exception as e:
    print(f"Error saving Ecut timestamp: {e}")

print("Done.")
