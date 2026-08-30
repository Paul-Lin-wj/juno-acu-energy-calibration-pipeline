"""
Centralized path & configuration for the recon module (Stage -1: rtraw -> ESD).

This module is pure ORCHESTRATION around the official junosw reconstruction:
it wraps `${TUTORIALROOT}/share/tut_rtraw2rec.py` (CVMFS J26.1.1) in a bash
environment wrapper and optionally overlays the optimized OMILRECV2 vertex/
energy algorithm (../omilrec_opt/omilrecv2). No reconstruction code lives
here; every flag below is frozen verbatim from the validated invocation
(omilrec_opt/v1.0/omilrec-v100-postv107-gated/scripts/generate_reference.sh,
see PROVENANCE.md) — numbers/flags are NOT to be edited casually.

Two implementations (--impl):
  omilrecv2  local reconstruction with the OMILRECV2 overlay (~8x faster
             vertex/energy; <=55 keV / 150 mm vs CVMFS baseline on 2/10
             sensitive events; NOT bit-identical)
  baseline   local reconstruction with the CVMFS J26.1.1 baseline OMILREC
             (the "official junosw" answer; slower)

Known open issue (see PROVENANCE.md): the frozen global tag is ReProd26A_v1
while the production ESD currently consumed by calibsel is ReProd26B.
"""

from pathlib import Path

# ============================================================
# Project root (auto-detected)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = PROJECT_ROOT.parent

# ============================================================
# Output layout (mirrors sibling modules):
#   output/<timestamp>/            (or --out-dir, no nested timestamp)
#     results/esd/RUN<N>/recon_RUN<N>_<i>.root   # ESD per rtraw file
#     results/esd_lists/esd_list_<N>.txt         # handoff to calibsel Stage 0
#     logs/  code/  config_snapshot.json  run_log.md  run_log.json
# ============================================================
OUTPUT_DIR = PROJECT_ROOT / "output"
ESD_SUBDIR = "results/esd"
ESD_LIST_SUBDIR = "results/esd_lists"

# ============================================================
# JUNO environment (needed ONLY inside the bash wrapper)
# ============================================================
# NOTE: J26.1.1 is what omilrecv2 builds against and what the validated
# invocation uses. calibsel Stage 0 (MySimpleTag) uses J26.3.1 — the two
# stages each source their own env in their own wrapper; do not "unify".
CVMFS_SETUP = "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.1.1/setup.sh"
ROOT_LIB = (
    "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.1.1/"
    "ExternalLibs/ROOT/6.30.08/lib"
)
XRD_STREAMTIMEOUT = 1200

# OMILRECV2 overlay (the optimization project; InstallArea must be built
# in place — `bash` rebuild instructions in its own README).
OMILRECV2_DIR = SUITE_ROOT.parent / "omilrec_opt" / "omilrecv2"
OMILRECV2_SETUP = OMILRECV2_DIR / "InstallArea" / "setup.sh"

# ============================================================
# Calibration maps / PDFs for OMILREC (Shubing Liu's files, local mirror
# by dingxf; sha256 pins from generate_reference.sh — verified 2026-08-27)
# ============================================================
MAPS_DIR = Path("/data/juno/dingxf/OMILREC_maps")
MAP_ASSETS = {  # relative path under MAPS_DIR -> sha256
    "nPEMap/LnPEMapFile_Ge68_Po214_reprod25D.root":
        "94ed84b08f21489f46089b605e24a6b53804bbc7adc66fca8b15aac55de16677",
    "TimePdf/TimePdfFile_236rbin_Ge68_2025comb_reprod26A.root":
        "eb161a6e5720bd061789edf984fc798eeb8a0f97b5faa5966cebe168c9d2c112",
    "TimePdf/TimePdfR3File_236rbin_fullLS.txt":
        "b9370e36fb49371e1f21502e134fd6e1cc85c62ebc9c44c13aaa010297f0c331",
    "ChargeSpec/average_pdf-12144.root":
        "0a0ff2cc50167599d207cb0fcb397b29b177d29862c6ef561b007c5f2d8166b7",
}

# ============================================================
# rtraw (raw DAQ) data on EOS — reachable via xrootd from this host
# ============================================================
XROOTD_HOST = "root://junoeos01.ihep.ac.cn"
XRDFS_HOST = "junoeos01.ihep.ac.cn"
XRDFS_BIN = (
    "/cvmfs/juno.ihep.ac.cn/el9_amd64_gcc11/Release/J26.3.1/"
    "ExternalLibs/xrootd/5.7.3/bin/xrdfs"
)
# Full DAQ archive, flat by date: <base>/<YYYY>/<MMDD>/RUN.<N>.JUNODAQ...rtraw
RTRAW_DAILY_BASE = "/eos/juno/rtraw"
# Curated per-version area (used by the colleague's workflow):
# <base>/<VER>/global_trigger/<NN000>/<NNN00>/<run>/
RTRAW_CURATED_BASE = "/eos/juno/juno-rtraw"
RTRAW_CURATED_VERSIONS = ["J25.7.1", "J25.7.0", "J25.5.0"]

# run -> date / source / position (owned by calibsel; read-only here)
CALIB_POS_FILE = SUITE_ROOT / "runcheck" / "data" / "CalibRUN_from_file.csv"

# ============================================================
# Frozen reconstruction flags (verbatim from the validated invocation;
# $TUTORIALROOT resolves inside the wrapper after sourcing CVMFS_SETUP)
# ============================================================
GLOBAL_TAG = "ReProd26A_v1"  # NOTE: production ESD we compare against is 26B
RECON_FLAGS = [
    "--calibstep-config", "$TUTORIALROOT/share/RecConfigs/waverec_calib_reprod.yaml",
    "--pmtcalibsvc-ChargeAlgType", "0",
    "--pmtcalibsvc-ReadDB", "1",
    "--global-tag", GLOBAL_TAG,
    "--method", "steering-v2",
    "--steering", "oec",
    "--use-mixedphase-in-steering",
    "--recstep-config",
    "$TUTORIALROOT/share/RecConfigs/evtrec_reprod_steering_using_OEC_woEcut.yaml",
    "--output-stream", "/Event/Oec:on",
    "--fullLSmode",
    "--enableRDTimePdf",
    "--RecMapPath", str(MAPS_DIR),
    "--RecMapFile", "LnPEMapFile_Ge68_Po214_reprod25D.root",
    "--TimePdfFile", "TimePdfFile_236rbin_Ge68_2025comb_reprod26A.root",
    "--TimePdfR3File", "TimePdfR3File_236rbin_fullLS.txt",
    "--AvgQPdfFile", "average_pdf-12144.root",
    "--cdcalibtq-npecut", "0.2",
    "--QPedThres", "0.2",
    "--OMILRECTQMode", "CalibNpeCut",
]

# ============================================================
# Defaults
# ============================================================
DEFAULT_IMPL = "omilrecv2"     # "omilrecv2" | "baseline"
DEFAULT_SLICE = 1              # rtraw files per run (1 = smoke-scale)
DEFAULT_EVTMAX = 100           # events per file (-1 = all)
TEST_RUN = 10110               # AmC117 center (x0y0z0), 2025-09-12
