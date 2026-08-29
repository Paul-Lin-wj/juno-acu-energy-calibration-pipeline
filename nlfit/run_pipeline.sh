#!/bin/bash
# =============================================================================
# run_pipeline.sh — nlfit one-click driver (Stages 4b, 5, 6, 7)
# =============================================================================
# Usage:
#   bash run_pipeline.sh --fitter-results <dir> [--out-dir <dir>] [flags]
#
# Requires nlfit/.venv (run setup_env.sh once). Stage 6 additionally needs
# the cvmfs ROOT environment from config/paths.py::CVMFS_SETUP and the
# dybmodel data (DYBMODEL_DATA; code is vendored in nlfit/dybmodel/); it is
# skipped with a clear error only when missing (use --skip-dybmodel to skip).
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -x .venv/bin/python ]; then
    echo "nlfit/.venv missing — running setup_env.sh"
    bash setup_env.sh
fi

exec .venv/bin/python pipeline/run_nlfit_all.py "$@"
