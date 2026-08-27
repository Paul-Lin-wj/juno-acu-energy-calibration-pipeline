#!/bin/bash
# =============================================================================
# run_pipeline.sh — sequential driver: esd2npz (selection) → fitter (fit)
#                   → nlfit (global NL fit + E_true=f(E_rec))
# =============================================================================
# Runs the full chain in ONE timestamped output directory:
#
#   <suite>/output/<YYYYmmdd_HHMMSS>/
#   ├── esd2npz/     # EDM→NPZ→26B correction→selection (run_log, cuts, code/)
#   ├── fitter/      # spectrum fitting (run_log, results, figures, code/)
#   └── nlfit/       # 4b contract → 5 aggregate → 6 dybmodel NL fit →
#                    # 7 E_rec→E_true lookup (run_log, results, figures, code/)
#
# Usage:
#   bash run_pipeline.sh                    # DEFAULT_RUNS of esd2npz (12370)
#   bash run_pipeline.sh 12370 12295        # explicit calibration runs
#   bash run_pipeline.sh --skip-qa          # extra flags pass through to esd2npz
#   RUNS="12370 12295" bash run_pipeline.sh # via env
#
# Requires the submodules' venvs to exist (run their setup_env.sh once).
# The fitter consumes the esd2npz selection NPZ of the SAME batch and the
# nlfit module the fitter results of the SAME batch — the hand-offs are
# fully self-contained (no output/latest dependency).

set -e
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$SUITE/output/$TS"
mkdir -p "$OUT/esd2npz" "$OUT/fitter" "$OUT/nlfit"

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
echo "=== [2/3] fitter: fit the selection NPZ → $OUT/fitter ==="
cd "$SUITE/fitter"
PY="$SUITE/fitter/.venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: fitter/.venv missing — run fitter/setup_env.sh first"; exit 1; }
"$PY" pipeline/run_fit_all.py --input-dir "$OUT/esd2npz/results/selection_npz" \
                              --out-dir "$OUT/fitter"

echo ""
echo "=== [3/3] nlfit: aggregate → dybmodel NL fit → E_true=f(E_rec) → $OUT/nlfit ==="
cd "$SUITE/nlfit"
NLFIT_FLAGS=(--fitter-results "$OUT/fitter/results" --out-dir "$OUT/nlfit")
# extra nlfit flags (e.g. --skip-dybmodel) via env: NLFIT_FLAGS="--skip-dybmodel"
if [ -n "$NLFIT_FLAGS" ]; then NLFIT_FLAGS+=($NLFIT_FLAGS); fi
bash run_pipeline.sh "${NLFIT_FLAGS[@]}"

echo ""
echo "=============================================="
echo "Joint run complete."
echo "Output root : $OUT"
echo "  esd2npz   : $OUT/esd2npz   (selection NPZ for the fitter)"
echo "  fitter    : $OUT/fitter    (fit results + ENL resolution plot)"
echo "  nlfit     : $OUT/nlfit     (gamma_AllPhase.dat + NL curves + E_true lookup)"
echo "=============================================="
