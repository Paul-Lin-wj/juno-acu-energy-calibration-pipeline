"""
Centralized path & default-mode configuration for standalone_esd2npz.

This is the ONLY file you need to edit when the environment changes.

Two kinds of settings:
  1. Local project paths  — data/output directories (usually no edit needed).
  2. External environment — CVMFS / lustrefs locations required ONLY by the
     optional ESD->EDM reconstruction stage (default pipeline skips it).

Default mode
------------
DEFAULT_MODE = "from-edm"  (recommended production default)
    Start from the pre-existing ReProd26B EDM chunks on lustrefs
    (REMOTE_EDM_DIR) and run  EDM -> NPZ -> 26B correction -> selection.
    This is the old "--skip-esd" behaviour, now the default: no CVMFS,
    no JUNOSW, no EOS access needed.

DEFAULT_MODE = "full-esd"
    Additionally reconstruct ESD -> EDM locally first (Stage 0; needs the
    external JUNO environment, hours per run). Selected with --full-esd.
"""

from pathlib import Path

# ============================================================
# Project root (auto-detected)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# Default pipeline mode ("from-edm" == old --skip-esd default)
# ============================================================
DEFAULT_MODE = "from-edm"          # "from-edm" | "full-esd"
DEFAULT_RUNS = [12370]             # runs used when none are given

# ============================================================
# Legacy in-project data dirs (fallbacks for manual src/ calls;
# the pipeline itself always writes into output/<timestamp>/)
# ============================================================
DATA_DIR          = PROJECT_ROOT / "data"
EDM_DIR           = DATA_DIR / "edm"          # stage 0 output: run_<RUN>_<i>_<j>.root
NPZ_RAW_DIR       = DATA_DIR / "npz_raw"      # stage 1 output: RUN<RUN>.npz
NPZ_CORRECTED_DIR = DATA_DIR / "npz_corrected"  # stage 2 output: RUN<RUN>.npz
SELECTION_DIR     = DATA_DIR / "selection"    # stage 3 output

# ============================================================
# Standard pipeline output layout (mirrors standalone_fitter)
#   output/<timestamp>/
#     results/npz_raw/  results/npz_corrected/  results/selection_npz/
#     results/timestamps/{Timestamp_wo_Ecut,Timestamp_Ecut}/
#     figures/selection/  figures/physics_qa/
#     cuts/  logs/  code_snapshot/
#     run_log.md  run_log.json  config_snapshot.json  console.log
# ============================================================
OUTPUT_DIR = PROJECT_ROOT / "output"

# Deliverable for downstream fitters (standalone_fitter DATA_INPUT_PATH
# should point at .../results/selection_npz).
SELECTION_NPZ_SUBDIR = "results/selection_npz"

# Finalcorrection correction data (copied into this project, self-contained)
CORRECTION_API_DIR = PROJECT_ROOT / "input" / "correction"
CORRECTION_DATA_DIR = CORRECTION_API_DIR / "data"

# Run -> source / background-run mapping (copied into this project)
CALIB_INFO_DIR      = PROJECT_ROOT / "calib_run_info"
CALIB_INFO_FILE     = CALIB_INFO_DIR / "calib_to_analyze.txt"
CALIB_POS_FILE      = CALIB_INFO_DIR / "CalibRUN_from_file.csv"

# ============================================================
# External environment (needed by the OPTIONAL ESD->EDM stage only)
# ============================================================
# JUNO offline software on CVMFS (provides python 3.11 + xrootd client tools).
CVMFS_SETUP = "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/setup.sh"
CVMFS_XROOTD_BIN = (
    "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/"
    "ExternalLibs/xrootd/5.7.3/bin"
)

# MySimpleTag reconstruction (ESD -> EDM), built from JUNOSW_MyAlgz.
JUNOSW_DIR   = Path("/lustrefs/juno26/users/zhaorz/Calib/JUNOSW_MyAlgz")
JUNOSW_SETUP = JUNOSW_DIR / "InstallArea" / "setup.sh"
RUN_PY       = JUNOSW_DIR / "SimpleTagAlgz" / "share" / "run.py"

# ESD files on EOS, reachable through the xrootd server.
XROOTD_HOST  = "root://junoeos01.ihep.ac.cn"
ESD_BASE     = "/eos/juno/juno-reprod/ReProd26B/global_trigger"

# Pre-existing EDM data (ReProd26B, all calib runs, 2799 chunks). This is the
# Stage-1 input in the default "from-edm" mode — the audited dataset whose
# chain to NPZ was verified bitwise-identical to the original production.
REMOTE_EDM_DIR = Path(
    "/lustrefs/juno26/users/zhaorz/Calib/ReProd26B/EDM_from_esd/Data"
)

# Fallback library dirs for the ESD->EDM stage (newer hosts lack libpcre.so.1).
LIB_FALLBACK_DIRS = [
    "/cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202105/lib",
    "/cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202002/lib",
]

# ============================================================
# Default test run
# ============================================================
TEST_RUN = 12370  # Ge68, 2025-12-17, 147 ESD files
