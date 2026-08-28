#!/bin/bash
# =============================================================================
# run_pipeline.sh — sequential driver:
#   recon (optional: rtraw→ESD local reconstruction via junosw/OMILRECV2)
#   → calibsel (γ singles + AmC correlated-pair selection)
#   → peakfit (γ peak fits + AmC nH/nC/O16)
#   → nlfit (global NL fit + E_true=f(E_rec))
# =============================================================================
# Runs the full chain in ONE timestamped output directory:
#
#   <suite>/output/<YYYYmmdd_HHMMSS>/
#   ├── recon/         # [可选] rtraw→ESD 本地重建（RECON_IMPL 启用；默认关，
#   │                 #   γ 分支直接用生产 ESD）
#   ├── calibsel/     # γ: EDM→NPZ→26B correction→selection (run_log, cuts, code/)
#   ├── calibsel_amc/ # AmC: (prompt,delayed) correlated-pair selection
#   ├── peakfit/      # γ peak fitting: RUN{N}_{src}.npz + ENL resolution plot
#   ├── peakfit_amc/  # AmC triple-peak fit (nH/nC/O16; npz merged into
#   │                 #   peakfit/results for nlfit — logs kept separate)
#   └── nlfit/        # 4b contract → 5 aggregate → 6 dybmodel NL fit →
#                     # 7 E_rec→E_true lookup (run_log, results, figures, code/)
#
# Usage:
#   bash run_pipeline.sh                    # default γ run (12370) + AmC 10110
#   bash run_pipeline.sh 12370 10110        # explicit runs (auto-routed by source)
#   bash run_pipeline.sh --skip-qa          # extra flags pass through to calibsel γ
#   RUNS="12370 12295" bash run_pipeline.sh   # 或经 RUNS/AMC_RUNS 环境变量给 run
#   DEFAULT_AMC_RUN=none bash run_pipeline.sh   # AmC 分支关闭
#   RECON_IMPL=omilrecv2 bash run_pipeline.sh   # 开启本地 rtraw→ESD 重建
#     # 规模: RECON_SLICE=1 RECON_EVTMAX=100（默认，冒烟级）
#     #       全量: RECON_SLICE=9999 RECON_EVTMAX=-1
#
# Run routing: each run number is looked up in
# calibsel/calib_run_info/calib_to_analyze.txt; AmC* sources → calibsel AmC
# branch + peakfit run_amc_fit_all, other sources → γ branch + run_fit_all.
# RECON note: 本地重建目前只服务 γ 分支（calibsel Stage 0 吃 recon 的
# esd_list）；AmC 走本地重建还需 run_all 出 npz_corrected（待 --corrections-only）。
# Requires the submodules' venvs to exist (run their setup_env.sh once).

set -e
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$SUITE/output/$TS"
mkdir -p "$OUT/recon" "$OUT/calibsel" "$OUT/calibsel_amc" "$OUT/peakfit" "$OUT/peakfit_amc" "$OUT/nlfit"

# collect run numbers (positional or RUNS/AMC_RUNS env) and pass the
# rest through to the γ branch.
# NOTE: 先捕获 env 再建同名数组 —— bash 中数组与标量共享命名空间，
# `RUNS=()` 会立刻清掉环境变量 RUNS。
RUNS_ENV="${RUNS:-}"
AMC_RUNS_ENV_STR="${AMC_RUNS:-}"
RUNS=()
GAMMA_FLAGS=()
for a in "$@"; do
    if [[ "$a" =~ ^[0-9]+$ ]]; then RUNS+=("$a"); else GAMMA_FLAGS+=("$a"); fi
done
if [ ${#RUNS[@]} -eq 0 ] && [ -n "$RUNS_ENV" ]; then RUNS=($RUNS_ENV); fi
if [ -n "$AMC_RUNS_ENV_STR" ]; then AMC_RUNS_ENV=($AMC_RUNS_ENV_STR); else AMC_RUNS_ENV=(); fi

# ---- route runs by source type (AmC* → AmC branch; rest → γ branch) ----
CALIB_INFO="$SUITE/calibsel/calib_run_info/calib_to_analyze.txt"
classify() {  # echo "AmC" or "gamma" for a run id
    "$SUITE/calibsel/.venv/bin/python" - "$1" "$CALIB_INFO" <<'PY'
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
AMC_RUNS=("${AMC_RUNS_ENV[@]}")
for r in "${RUNS[@]}"; do
    src=$(classify "$r" 2>/dev/null) || src="gamma"
    if [ "$src" = "AmC" ]; then AMC_RUNS+=("$r"); else GAMMA_RUNS+=("$r"); fi
done
# 显式给过 run（位置参数或 RUNS env）则不再自动补默认 AmC
EXPLICIT_RUNS=1
if [ ${#RUNS[@]} -eq 0 ] && [ ${#AMC_RUNS[@]} -eq 0 ]; then EXPLICIT_RUNS=0; fi
# 默认补一个 AmC 中心 run（仅当未显式给任何 run 且输入预置于
# calibsel/input/amc_data/ 时）；DEFAULT_AMC_RUN=none 关闭
if [ $EXPLICIT_RUNS -eq 0 ] && [ "${DEFAULT_AMC_RUN-10110}" != "none" ] \
   && [ -f "$SUITE/calibsel/input/amc_data/RUN${DEFAULT_AMC_RUN-10110}.npz" ]; then
    AMC_RUNS+=("${DEFAULT_AMC_RUN-10110}")
fi
echo "gamma runs: ${GAMMA_RUNS[*]:-<none>}   AmC runs: ${AMC_RUNS[*]:-<none>}"

# ---------------- [0/6] recon (optional): rtraw → ESD ----------------
# RECON_IMPL=omilrecv2|baseline 开启本地重建（默认关闭 = 用生产 ESD）。
# 产物 ESD 清单传给 calibsel γ 分支（--full-esd --esd-list-dir）。
RECON_ESD_LIST_DIR=""
if [ -n "${RECON_IMPL:-}" ]; then
    RECON_RUNS=(${GAMMA_RUNS[@]} ${AMC_RUNS[@]})
    if [ ${#RECON_RUNS[@]} -gt 0 ]; then
        echo ""
        echo "=== [0/6] recon ($RECON_IMPL): rtraw → ESD → $OUT/recon ==="
        cd "$SUITE/recon"
        bash run_pipeline.sh "${RECON_RUNS[@]}" --impl "$RECON_IMPL" \
            --slice "${RECON_SLICE:-1}" --evtmax "${RECON_EVTMAX:-100}" \
            --out-dir "$OUT/recon"
        RECON_ESD_LIST_DIR="$OUT/recon/results/esd_lists"
    else
        echo "=== [0/6] recon: skipped (no runs given) ==="
    fi
else
    echo ""
    echo "=== [0/6] recon: skipped (RECON_IMPL unset — using production ESD) ==="
fi

# ---------------- [1/6] calibsel γ branch ----------------
# （未给 run 时保留 calibsel 自己的 DEFAULT_RUNS 默认；显式只给 AmC run 时跳过）
if [ ${#GAMMA_RUNS[@]} -gt 0 ] || [ ${#RUNS[@]} -eq 0 ]; then
    echo ""
    echo "=== [1/6] calibsel (gamma): EDM → selection NPZ → $OUT/calibsel ==="
    cd "$SUITE/calibsel"
    CALIBSEL_ARGS=("${GAMMA_RUNS[@]}" "${GAMMA_FLAGS[@]}" --out-dir "$OUT/calibsel")
    if [ -n "$RECON_ESD_LIST_DIR" ] && [ ${#GAMMA_RUNS[@]} -gt 0 ]; then
        # recon 本地重建的 ESD 清单（含 Stage 0；本底 run 需一并重建）
        CALIBSEL_ARGS+=(--full-esd --esd-list-dir "$RECON_ESD_LIST_DIR")
    fi
    bash run_pipeline.sh "${CALIBSEL_ARGS[@]}"
    GAMMA_SELECTION_DIR="$OUT/calibsel/results/selection_npz"
else
    echo ""
    echo "=== [1/6] calibsel (gamma): skipped (no gamma runs) ==="
    GAMMA_SELECTION_DIR=""
fi

# ---------------- [2/6] calibsel AmC branch ----------------
AMC_CORR_NPZ=""
if [ ${#AMC_RUNS[@]} -gt 0 ]; then
    echo ""
    echo "=== [2/6] calibsel (AmC): correlated pairs → $OUT/calibsel_amc ==="
    cd "$SUITE/calibsel"
    [ -x .venv/bin/python ] || bash setup_env.sh
    for r in "${AMC_RUNS[@]}"; do
        # 输入优先用本批 γ 分支的 26B 修正输出，否则用预置 input/amc_data
        INPUT_DIR="$SUITE/calibsel/input/amc_data"
        if [ -f "$OUT/calibsel/results/npz_corrected/RUN$r.npz" ]; then
            INPUT_DIR="$OUT/calibsel/results/npz_corrected"
        fi
        .venv/bin/python pipeline/run_amcsel_all.py --run "$r" \
            --input-dir "$INPUT_DIR" --out-dir "$OUT/calibsel_amc"
        AMC_CORR_NPZ="$OUT/calibsel_amc/results/RUN$r/correlation_result_RUN$r.npz"
    done
else
    echo ""
    echo "=== [2/6] calibsel (AmC): skipped (no AmC runs) ==="
fi

# ---------------- [3/6] peakfit: γ peaks ----------------
echo ""
echo "=== [3/6] peakfit (gamma): peak fits → $OUT/peakfit ==="
cd "$SUITE/peakfit"
PY="$SUITE/peakfit/.venv/bin/python"
[ -x "$PY" ] || { echo "ERROR: peakfit/.venv missing — run peakfit/setup_env.sh first"; exit 1; }
if [ -n "$GAMMA_SELECTION_DIR" ]; then
    "$PY" pipeline/run_fit_all.py --input-dir "$GAMMA_SELECTION_DIR" \
                                  --out-dir "$OUT/peakfit"
fi

# ---------------- [4/6] peakfit: AmC triple peak ----------------
if [ -n "$AMC_CORR_NPZ" ]; then
    echo ""
    echo "=== [4/6] peakfit (AmC): nH/nC/O16 → $OUT/peakfit_amc ==="
    r="${AMC_RUNS[-1]}"
    # AmC 拟合单独留档（避免与 γ 拟合的 run_log 互相覆盖），
    # 结果 npz 汇入 $OUT/peakfit/results 供 nlfit 统一消费
    "$PY" pipeline/run_amc_fit_all.py --run "$r" --corr-npz "$AMC_CORR_NPZ" \
                                      --out-dir "$OUT/peakfit_amc"
    mkdir -p "$OUT/peakfit/results"
    cp "$OUT"/peakfit_amc/results/RUN"${r}"_*.npz "$OUT/peakfit/results/"
else
    echo ""
    echo "=== [4/6] peakfit (AmC): skipped ==="
fi

# ---------------- [5/6] nlfit: aggregate → dybmodel → lookup ----------------
echo ""
echo "=== [5/6] nlfit: aggregate → dybmodel NL fit → E_true=f(E_rec) → $OUT/nlfit ==="
cd "$SUITE/nlfit"
NLFIT_ARGS=(--fitter-results "$OUT/peakfit/results" --out-dir "$OUT/nlfit")
# extra nlfit flags (e.g. --skip-dybmodel) via env: NLFIT_FLAGS="--skip-dybmodel"
if [ -n "$NLFIT_FLAGS" ]; then NLFIT_ARGS+=($NLFIT_FLAGS); fi
bash run_pipeline.sh "${NLFIT_ARGS[@]}"

echo ""
echo "=============================================="
echo "Joint run complete."
echo "Output root : $OUT"
echo "  recon       : $OUT/recon       (only if RECON_IMPL set: local rtraw→ESD)"
echo "  calibsel    : $OUT/calibsel    (selection NPZ for peakfit)"
echo "  calibsel_amc: $OUT/calibsel_amc (correlation_result_RUN{N}.npz)"
echo "  peakfit     : $OUT/peakfit     (RUN{N}_{src}.npz incl. nH/nC/AmC + ENL plot)"
echo "  nlfit       : $OUT/nlfit       (gamma_AllPhase.dat + NL curves + E_true lookup)"
echo "=============================================="
