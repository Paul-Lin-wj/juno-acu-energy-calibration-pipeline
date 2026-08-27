#!/bin/bash
# =============================================================================
# run_pipeline.sh — sequential driver:
#   esd2npz (gamma selection) → fitter (gamma fit)
#   amcsel (AmC pair selection) → fitter (nH/nC/O16 fit)
#   → nlfit (global NL fit + E_true=f(E_rec))
# =============================================================================
# Runs the full chain in ONE timestamped output directory:
#
#   <suite>/output/<YYYYmmdd_HHMMSS>/
#   ├── esd2npz/     # EDM→NPZ→26B correction→selection (run_log, cuts, code/)
#   ├── fitter/      # spectrum fitting: RUN{N}_{src}.npz (gamma + AmC 三峰)
#   ├── amcsel/      # AmC (prompt,delayed) 关联对挑选（仅当有 AmC run）
#   └── nlfit/       # 4b contract → 5 aggregate → 6 dybmodel NL fit →
#                    # 7 E_rec→E_true lookup (run_log, results, figures, code/)
#
# Usage:
#   bash run_pipeline.sh                    # DEFAULT_RUNS of esd2npz (12370)
#                                           #   + DEFAULT_AMC_RUN (10110, 若
#                                           #   amcsel/input/Data 有数据)
#   bash run_pipeline.sh 12370 10110        # explicit runs (auto-routed by source)
#   bash run_pipeline.sh --skip-qa          # extra flags pass through to esd2npz
#   RUNS="12370 12295" AMC_RUNS= bash run_pipeline.sh
#
# Run routing: each run number is looked up in calib_run_info/calib_to_analyze.txt;
# AmC* sources → amcsel + run_amc_fit_all, other sources → esd2npz + run_fit_all.
# Requires the submodules' venvs to exist (run their setup_env.sh once).

set -e
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$SUITE/output/$TS"
mkdir -p "$OUT/esd2npz" "$OUT/fitter" "$OUT/nlfit" "$OUT/amcsel" "$OUT/fitter_amc"

# collect run numbers (positional) and pass the rest through to esd2npz
RUNS=()
ESD2NPZ_FLAGS=()
for a in "$@"; do
    if [[ "$a" =~ ^[0-9]+$ ]]; then RUNS+=("$a"); else ESD2NPZ_FLAGS+=("$a"); fi
done

# ---- route runs by source type (AmC* → amcsel; rest → esd2npz) ----
CALIB_INFO="$SUITE/amcsel/calib_run_info/calib_to_analyze.txt"
classify() {  # echo "AmC" or "gamma" for a run id
    "$SUITE/amcsel/.venv/bin/python" - "$1" "$CALIB_INFO" <<'PY'
import sys
run, path = int(sys.argv[1]), sys.argv[2]
for line in open(path):
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2 or not parts[0]:
        continue
    rng = parts[1]
    try:
        lo, hi = (map(int, rng.split("-")) if "-" in rng else (int(rng), int(rng)))
    except ValueError:
        continue
    if lo <= run <= hi:
        print("AmC" if "Am" in parts[0] or "Cf" in parts[0] else "gamma")
        break
PY
}
GAMMA_RUNS=()
AMC_RUNS=()
for r in "${RUNS[@]}"; do
    src=$(classify "$r" 2>/dev/null) || src="gamma"
    if [ "$src" = "AmC" ]; then AMC_RUNS+=("$r"); else GAMMA_RUNS+=("$r"); fi
done
# 默认补一个 AmC 中心 run（输入预置于 amcsel/input/Data 时），
# 可用 DEFAULT_AMC_RUN=none 或提供自己的 AmC run 覆盖
if [ ${#AMC_RUNS[@]} -eq 0 ] && [ "${DEFAULT_AMC_RUN-10110}" != "none" ] \
   && [ -f "$SUITE/amcsel/input/Data/RUN${DEFAULT_AMC_RUN-10110}.npz" ]; then
    AMC_RUNS+=("${DEFAULT_AMC_RUN-10110}")
fi
echo "gamma runs: ${GAMMA_RUNS[*]:-<none>}   AmC runs: ${AMC_RUNS[*]:-<none>}"

# ---------------- [1/4] esd2npz: gamma selection ----------------
# （未给 run 时保留 esd2npz 自己的 DEFAULT_RUNS 默认；显式只给 AmC run 时跳过）
if [ ${#GAMMA_RUNS[@]} -gt 0 ] || [ ${#RUNS[@]} -eq 0 ]; then
    echo ""
    echo "=== [1/4] esd2npz: EDM → selection NPZ → $OUT/esd2npz ==="
    cd "$SUITE/esd2npz"
    bash run_pipeline.sh "${GAMMA_RUNS[@]}" "${ESD2NPZ_FLAGS[@]}" --out-dir "$OUT/esd2npz"
    GAMMA_SELECTION_DIR="$OUT/esd2npz/results/selection_npz"
else
    echo ""
    echo "=== [1/4] esd2npz: skipped (no gamma runs) ==="
    GAMMA_SELECTION_DIR=""
fi

# ---------------- [2/4] amcsel: AmC correlated pairs ----------------
AMC_CORR_NPZ=""
if [ ${#AMC_RUNS[@]} -gt 0 ]; then
    echo ""
    echo "=== [2/4] amcsel: AmC (prompt,delayed) selection → $OUT/amcsel ==="
    cd "$SUITE/amcsel"
    [ -x .venv/bin/python ] || bash setup_env.sh
    for r in "${AMC_RUNS[@]}"; do
        # 输入优先用本批 esd2npz 的 26B 修正输出，否则用预置 amcsel/input/Data
        INPUT_DIR="$SUITE/amcsel/input/Data"
        if [ -f "$OUT/esd2npz/results/npz_corrected/RUN$r.npz" ]; then
            INPUT_DIR="$OUT/esd2npz/results/npz_corrected"
        fi
        .venv/bin/python pipeline/run_amcsel_all.py --run "$r" \
            --input-dir "$INPUT_DIR" --out-dir "$OUT/amcsel"
        AMC_CORR_NPZ="$OUT/amcsel/results/RUN$r/correlation_result_RUN$r.npz"
    done
else
    echo ""
    echo "=== [2/4] amcsel: skipped (no AmC runs) ==="
fi

# ---------------- [3/4] fitter: gamma + AmC peaks ----------------
echo ""
echo "=== [3/4] fitter: peak fits → $OUT/fitter ==="
cd "$SUITE/fitter"
PY="$SUITE/fitter/.venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: fitter/.venv missing — run fitter/setup_env.sh first"; exit 1; }
if [ -n "$GAMMA_SELECTION_DIR" ]; then
    "$PY" pipeline/run_fit_all.py --input-dir "$GAMMA_SELECTION_DIR" \
                                  --out-dir "$OUT/fitter"
fi
if [ -n "$AMC_CORR_NPZ" ]; then
    r="${AMC_RUNS[-1]}"
    # AmC 拟合单独留档（避免与 gamma 拟合的 run_log 互相覆盖），
    # 结果 npz 汇入 $OUT/fitter/results 供 nlfit 统一消费
    "$PY" pipeline/run_amc_fit_all.py --run "$r" --corr-npz "$AMC_CORR_NPZ" \
                                      --out-dir "$OUT/fitter_amc"
    mkdir -p "$OUT/fitter/results"
    cp "$OUT"/fitter_amc/results/RUN"${r}"_*.npz "$OUT/fitter/results/"
fi

# ---------------- [4/4] nlfit: aggregate → dybmodel → lookup ----------------
echo ""
echo "=== [4/4] nlfit: aggregate → dybmodel NL fit → E_true=f(E_rec) → $OUT/nlfit ==="
cd "$SUITE/nlfit"
NLFIT_ARGS=(--fitter-results "$OUT/fitter/results" --out-dir "$OUT/nlfit")
# extra nlfit flags (e.g. --skip-dybmodel) via env: NLFIT_FLAGS="--skip-dybmodel"
if [ -n "$NLFIT_FLAGS" ]; then NLFIT_ARGS+=($NLFIT_FLAGS); fi
bash run_pipeline.sh "${NLFIT_ARGS[@]}"

echo ""
echo "=============================================="
echo "Joint run complete."
echo "Output root : $OUT"
echo "  esd2npz   : $OUT/esd2npz   (selection NPZ for the fitter)"
echo "  amcsel    : $OUT/amcsel    (correlation_result_RUN{N}.npz)"
echo "  fitter    : $OUT/fitter    (RUN{N}_{src}.npz incl. nH/nC/AmC + ENL plot)"
echo "  nlfit     : $OUT/nlfit     (gamma_AllPhase.dat + NL curves + E_true lookup)"
echo "=============================================="
