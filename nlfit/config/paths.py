"""
Centralized path & physics configuration for the nlfit (nonlinearity fit) module.

Only this file needs editing when the environment changes.
"""
from pathlib import Path

# ============================================================
# Project root (auto-detected from this file's location)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = PROJECT_ROOT.parent

# ============================================================
# Input: fitter results directory (contains RUN{N}_{source}.npz)
# Default points at the joint-run layout output/<ts>/fitter/results.
# ============================================================
FITTER_RESULTS_DIR = SUITE_ROOT / "fitter" / "output" / "latest" / "results"

# ============================================================
# External inputs contract (Stage 4b)
# Interim values for peaks this repo cannot yet produce
# (n-H / n-12C / O16 come from the AmC chain; continuous spectra from
# the prepared Isotope root file). MANIFEST carries sha256 + provenance.
# ============================================================
EXTERNAL_INPUTS_DIR = PROJECT_ROOT / "external_inputs"
EXTERNAL_MANIFEST = EXTERNAL_INPUTS_DIR / "MANIFEST.json"
# key in MANIFEST["files"] holding the historical 7-peak table
HISTORICAL_GAMMA_KEY = "gamma_peaks_historical_AllPhase.dat"

# ============================================================
# The 7 gamma peaks entering fitter_energynl_dybmodel, in the FIXED
# order expected by dybGammaData::LoadData (one "mu err_mu_rel" per line).
#   provider = "fitter"  -> mu from <fitter results>/RUN{run}_{key}.npz
#              "external"-> mu from the MANIFEST historical table (pinned)
# e_true follows the dyb convention (Ge68 = annihilation pair 1.022 MeV,
# Co60 = cascade sum 2.506 MeV) — NOTE: differs from the fitter's internal
# E_scale anchor for Ge68 (0.8845), which is not a physics true energy.
# ============================================================
PEAKS = [
    # key      e_true   provider    run_id (fitter provider only)
    ("Cs137",  0.6617,  "fitter",   12295),
    ("Mn54",   0.8348,  "fitter",   12247),
    ("Ge68",   1.022,   "fitter",   12370),
    ("nH",     2.2233,  "external", None),
    ("Co60",   2.506,   "fitter",   12216),
    ("nC",     4.95,    "external", None),
    ("O16",    6.129,   "external", None),
]
# K40 is fitted by this suite but is NOT one of the 7 dybmodel gamma peaks
# (it enters the fit as a spectrum via K40.root); listed for provenance only.
FITTER_ONLY_SOURCES = ["K40"]

# Warn (not fail) when a fitter-provided mu deviates from the historical
# value by more than this fraction (different run periods expected).
MU_DEVIATION_WARN = 0.05

# The dat's err_mu column is the TOTAL relative error (stat ⊕ sys) in the
# historical convention (all 7 peaks pinned at 0.005). The fitter gives us
# a statistical-only error (e.g. 2e-4 for Ge68) which would over-constrain
# the global fit, so floor it — set to 0 to disable.
MU_ERR_FLOOR = 0.005

# ============================================================
# dybmodel C++ fitter — ORIGINAL tree, run in OUR OWN container.
#
# Assets staged on /datafs by tools/setup_container.sh (see container/):
#   sl69worknode20240820.sif : byte-identical copy of the official IHEP
#                              SL6 worknode image (provenance / def source)
#   rootfs/                   : unsquashfs extraction of that SIF, used as
#                              the apptainer sandbox at runtime
#   juno-sl6-amd64-gcc447/    : the ROOT5-era J17v1r1 release, with its
#                              text setup scripts' hardcoded /cvmfs paths
#                              rewritten to this staging directory
#                              (binaries untouched; only env-script paths)
#
# Runtime quirks this layout works around on this node family:
#   - /cvmfs/juno.ihep.ac.cn on the HOST is a publicfs disk pretending to
#     be cvmfs (no sl6 content); unprivileged userns containers inherit
#     that mount and cannot shadow it -> J17 lives on /datafs instead
#   - any in-container directory NAMED like a cvmfs repo gets the host
#     repo mounted over it -> the staging dir avoids repo names
#
# The C++ code is NEVER modified: the per-run gamma table is placed at the
# canonical necessaryfiles path inside a per-run symlink-farm sandbox.
# ============================================================
DYBMODEL_SRC = Path("/datafs/users/wujxy/agent-sci/ENL_agent/fitter_energynl_dybmodel")

# Container assets (staged outside the repo; see tools/setup_container.sh)
DYBMODEL_CONTAINER_DIR = Path("/datafs/users/wujxy/containers/dybmodel-sl6")
DYBMODEL_SIF = DYBMODEL_CONTAINER_DIR / "sl69worknode20240820.sif"
DYBMODEL_ROOTFS = DYBMODEL_CONTAINER_DIR / "rootfs"
DYBMODEL_J17 = (DYBMODEL_CONTAINER_DIR / "juno-sl6-amd64_gcc447" /
                "Release" / "J17v1r1")
DYBMODEL_J17_SETUP = str(DYBMODEL_J17 / "setup.sh")  # host==container path
APPTAINER = "apptainer"
DYBMODEL_SIF_SHA256 = ("50c6aff2278a7d85dd69c985d326bbb69b1f8387b"
                       "d22fafa412b7c07f7d4cd4b")  # see container/SHA256SUMS

# Local el9 ROOT env — used ONLY for tools/dump_curves.C (TSV export)
CVMFS_SETUP = "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.1.1/setup.sh"

# Output subpaths of dybmodel (CWD-relative inside the run sandbox);
# toyKey must match dybParameters.cxx (output file naming only).
DYB_TOY_KEY = "nom_JUNO_26B_finalCorrection_AllPhase_FVcutR0_1720"
DYB_FIT_TIMEOUT_S = 3600

# ============================================================
# Output directories (relative to the --out-dir given by the orchestrator)
# ============================================================
OUTPUT_RES_DIR = "results"     # gamma_AllPhase.dat, bestFit, curves.tsv, lookup
OUTPUT_FIG_DIR = "figures"     # intermediate QC plots (per stage)
OUTPUT_WORK_DIR = "_work"      # dybmodel run sandbox (deleted on success)

# Curve names dumped from curves_<toyKey>.root (Stage 7 input)
CURVE_NAMES = [
    "electronicsNL", "electronScintNL", "positronScintNL", "gammaScintNL",
    "alphaScintNL", "electronFullNL", "positronFullNL", "gammaFullNL",
    "alphaFullNL",
]
# Curves that get an E_true = f(E_rec) lookup table in Stage 7
INVERT_CURVES = ["gammaFullNL", "electronFullNL", "positronFullNL"]
