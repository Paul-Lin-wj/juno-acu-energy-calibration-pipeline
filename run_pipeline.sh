#!/bin/bash
# =============================================================================
# run_pipeline.sh — sequential driver: esd2npz (selection) → fitter (fit)
# =============================================================================
# Runs the full chain in ONE timestamped output directory:
#
#   <suite>/output/<YYYYmmdd_HHMMSS>/
#   ├── esd2npz/     # EDM→NPZ→26B correction→selection (run_log, cuts, code/)
#   └── fitter/      # spectrum fitting (run_log, results, figures, code/)
#
# Usage:
#   bash run_pipeline.sh                    # DEFAULT_RUNS of esd2npz (12370)
#   bash run_pipeline.sh 12370 12295        # explicit calibration runs
#   bash run_pipeline.sh --skip-qa          # extra flags pass through to esd2npz
#   RUNS="12370 12295" bash run_pipeline.sh # via env
#
# Requires both submodules' venvs to exist (run their setup_env.sh once).
# The fitter consumes the esd2npz selection NPZ of the SAME batch, so the
# hand-off is fully self-contained (no output/latest dependency).

set -e
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$SUITE/output/$TS"
mkdir -p "$OUT/esd2npz" "$OUT/fitter"

# collect run numbers (positional) and pass the rest through to esd2npz
RUNS=()
ESD2NPZ_FLAGS=()
for a in "$@"; do
    if [[ "$a" =~ ^[0-9]+$ ]]; then RUNS+=("$a"); else ESD2NPZ_FLAGS+=("$a"); fi
done

echo "=== [1/2] esd2npz: EDM → selection NPZ → $OUT/esd2npz ==="
cd "$SUITE/esd2npz"
bash run_pipeline.sh "${RUNS[@]}" "${ESD2NPZ_FLAGS[@]}" --out-dir "$OUT/esd2npz"

echo ""
echo "=== [2/2] fitter: fit the selection NPZ → $OUT/fitter ==="
cd "$SUITE/fitter"
PY="$SUITE/fitter/.venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: fitter/.venv missing — run fitter/setup_env.sh first"; exit 1; }
"$PY" pipeline/run_fit_all.py --input-dir "$OUT/esd2npz/results/selection_npz" \
                              --out-dir "$OUT/fitter"

echo ""
echo "=============================================="
echo "Joint run complete."
echo "Output root : $OUT"
echo "  esd2npz   : $OUT/esd2npz   (selection NPZ for the fitter)"
echo "  fitter    : $OUT/fitter    (fit results + ENL resolution plot)"
echo "=============================================="
