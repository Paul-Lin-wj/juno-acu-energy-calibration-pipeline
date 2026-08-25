#!/bin/bash
# =============================================================================
# run_pipeline.sh — one-click ESD/EDM -> selection-NPZ pipeline
# =============================================================================
# Usage:
#   bash run_pipeline.sh                     # default runs, default mode
#   bash run_pipeline.sh 12370 12295         # specific runs
#   bash run_pipeline.sh 12370 --full-esd    # also reconstruct ESD->EDM
#   bash run_pipeline.sh 12370 --slice 3     # ESD smoke test (3 files)
#
# Default mode ("from-edm") starts from the pre-existing ReProd26B EDM chunks
# on lustrefs — no CVMFS/JUNOSW/EOS needed. All extra args are passed to
# pipeline/run_all.py (--skip-bkg, --skip-qa, --edm-input DIR, ...).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${SCRIPT_DIR}/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[Info] Virtual environment not found. Running setup_env.sh..."
    bash setup_env.sh
fi

PY="${VENV_DIR}/bin/python"

# Split positional args (run numbers) from flags; flags go to run_all.py
RUN_ARGS=()
PASS_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --out-dir|--edm-input)
            PASS_ARGS+=("$1" "$2"); shift 2 ;;
        --*)
            PASS_ARGS+=("$1"); shift ;;
        *)
            RUN_ARGS+=("$1"); shift ;;
    esac
done
if [ ${#RUN_ARGS[@]} -gt 0 ]; then
    PASS_ARGS=("${PASS_ARGS[@]}" --runs "${RUN_ARGS[@]}")
fi

echo "[Info] Using python: $PY"
exec "$PY" pipeline/run_all.py "${PASS_ARGS[@]}"
