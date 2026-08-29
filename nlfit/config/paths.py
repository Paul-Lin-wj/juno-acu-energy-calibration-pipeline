"""
Centralized path & physics configuration for the nlfit (nonlinearity fit) module.

Only this file needs editing when the environment changes.
"""
import os
from pathlib import Path

# ============================================================
# Project root (auto-detected from this file's location)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = PROJECT_ROOT.parent

# ============================================================
# Input: peakfit results directory (contains RUN{N}_{source}.npz)
# Default points at the joint-run layout output/<ts>/peakfit/results.
# ============================================================
FITTER_RESULTS_DIR = SUITE_ROOT / "peakfit" / "output" / "latest" / "results"

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
#   provider = "fitter"  -> mu from <peakfit results>/RUN{run}_{key}.npz
#              "external"-> mu from the MANIFEST historical table (pinned)
# e_true follows the dyb convention (Ge68 = annihilation pair 1.022 MeV,
# Co60 = cascade sum 2.506 MeV) — NOTE: differs from the fitter's internal
# E_scale anchor for Ge68 (0.8845), which is not a physics true energy.
# ============================================================
PEAKS = [
    # key      e_true   provider    run_id (fitter/amc providers)
    ("Cs137",  0.6617,  "fitter",   12295),
    ("Mn54",   0.8348,  "fitter",   12247),
    ("Ge68",   1.022,   "fitter",   12370),
    # AmC 关联对三峰（RUN10110 = AmC117 @ 中心 Z=0，BKG 10100）：
    # calibsel AmC 支线(Stage3c) -> peakfit run_amc_fit_all(Stage3b) -> 本处
    ("nH",     2.2233,  "amc",      10110),
    ("Co60",   2.506,   "fitter",   12216),
    ("nC",     4.95,    "amc",      10110),
    ("O16",    6.129,   "amc",      10110),
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
# Per-phase mode:  --phase {all,1,2,3,4}
#
# DESIGN CONTRACT — adding a NEW phase stays data-driven (files, not
# code), with exactly ONE mapping line to add here (step 3):
#   1. calibsel/input/correction/data/ValProd26BPhase.csv — add the run
#      range row. This csv is the single source of truth: the 26B
#      correction AND nlfit's --phase choices both read it.
#      (Needs the colleague deliverables phase{N}_model.npz + absolute
#      energy scale under calibsel/input/correction/ — cannot be
#      self-generated; out-of-range runs fall back to the NEAREST phase,
#      see correction_api.phase_from_run.)
#   2. calibsel/calib_run_info/{CalibRUN_from_file.csv,
#      calib_to_analyze.txt} — the new phase's runs (production-side
#      updates anyway).
#   3. dybmodel necessaryfiles .../Spec/forNLfitter/ — add the phase's
#      Isotope_data_Phase{N}_*.root (colleague deliverable) AND one line
#      in ISOTOPE_ROOT_BY_PHASE below.
#   4. Run:  nlfit --phase N  (run selection is automatic — the phase's
#      centre runs, |z| <= CENTRE_Z_MAX, inverse-variance weighted mean
#      per source; absent sources are EXCLUDED, not pinned).
# ============================================================
PHASE_TABLE = (SUITE_ROOT / "calibsel" / "input" / "correction" / "data" /
               "ValProd26BPhase.csv")
CALIB_RUN_TABLE = (SUITE_ROOT / "calibsel" / "calib_run_info" /
                   "CalibRUN_from_file.csv")

# centre-run convention for automatic per-phase selection (matches the
# production analysis: meanEscaleEres_perPhase_CDcenter)
CENTRE_Z_MAX = 0.5

# Production pinned nC to this value in ALL gamma_*.dat tables
# (glue/gen_gamma_dat.py --override nC=5.08140). Our default is the
# measured nC; pass --nc-pin to reproduce the production caliber exactly.
NC_PIN = 5.08140

# The C++ opens ONE fixed filename (dybParameters.cxx:199-201, b12/c11/c10
# share it). Per-phase isotope spectra are placed AT this canonical path
# as a real copy inside the per-run sandbox — the colleague's tree is
# never touched and no rebuild is needed.
ISOTOPE_CANONICAL = ("Isotope_data_AllPhase_FVcutR0_1720_"
                     "Finalcorrection.root")
SPEC_FORNL_RELDIR = "input/JUNO/ReProd26B/Spec/forNLfitter"

# Per-phase isotope spectra — same FVcutR0_1720 + Finalcorrection caliber
# as the AllPhase default (all four already exist in the colleague tree).
# NEW PHASE: drop the root into Spec/forNLfitter/ and add one line here.
ISOTOPE_ROOT_BY_PHASE = {
    1: "Isotope_data_Phase1_FVcutR0_1720_Finalcorrection.root",
    2: "Isotope_data_Phase2_FVcutR0_1720_Finalcorrection.root",
    3: "Isotope_data_Phase3_FVcutR0_1720_Finalcorrection.root",
    4: "Isotope_data_Phase4_FVcutR0_1720_Finalcorrection.root",
}

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
# ============================================================
# dybmodel fitter — vendored CODE (in-repo) + staged DATA (out of git)
#
#   nlfit/dybmodel/            src/ include/ Makefile run.sh — VERBATIM
#                              copy of the C++ (byte-verified against
#                              ENL_FITTER_COMMIT), plus reference/ (the
#                              behaviour-lock bestFit) and
#                              MINIMAL_RUN_LIST.md (upstream cursor note).
#   DYBMODEL_DATA_DIR          773 MB necessaryfiles/ + the prebuilt
#                              1.4 MB `fitter` binary — NOT in git.
#                              Populate with tools/fetch_dybmodel_data.sh
#                              (default nlfit/dybmodel_data/, gitignored;
#                              override with $DYBMODEL_DATA).
#
# The binary is sha-pinned (not rebuilt) so the behaviour lock holds:
# original binary + our container + historical gamma table -> bestFit
# byte-identical to the 2026-08-16 baseline (see PROVENANCE notes).
# ============================================================
DYBMODEL_CODE_DIR = PROJECT_ROOT / "dybmodel"
DYBMODEL_DATA_DIR = Path(os.environ.get("DYBMODEL_DATA")
                         or PROJECT_ROOT / "dybmodel_data")
ENL_FITTER_REPO = "git@github.com:wujxy/ENL_fitter.git"   # upstream mirror
ENL_FITTER_COMMIT = "2f487f9a21843e8f86db338d8d3ef884e179dde5"
DYBMODEL_BIN_SHA256 = ("9d36caac71f2f5651503819115e5555cae66d0eb"
                       "16c48e057a990c403f336be2")
# Quenching.root (364 MB) is NOT in the upstream HEAD tree — it exists
# only in commit cda3b93b; fetch_dybmodel_data.sh recovers it from there.
QUENCHING_SHA256 = ("92a9d4d05f53cec24d3f31a14ec136ec4b0871c2"
                    "de89bedf22716ecf79a4319a")
QUENCHING_RECOVER_COMMIT = "cda3b93b"

# Container assets (staged outside the repo; see tools/setup_container.sh —
# honour the same env override the setup script uses for non-/datafs nodes)
DYBMODEL_CONTAINER_DIR = Path(os.environ.get("DYBMODEL_CONTAINER_DIR")
                              or "/datafs/users/wujxy/containers/dybmodel-sl6")
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
