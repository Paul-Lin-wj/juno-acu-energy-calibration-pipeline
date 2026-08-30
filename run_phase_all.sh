#!/bin/bash
# =============================================================================
# run_phase_all.sh — phase-by-phase 非线性拟合复刻驱动
# =============================================================================
# 对每个 phase：解析该 phase 的刻度源中心 run（与 nlfit --phase 同一张
# 事实源表、同一口径），让顶层 run_pipeline.sh 把四段链
# (calibsel → peakfit γ → peakfit AmC → nlfit) 按该 phase 的 run 子集跑完，
# nlfit 以 --phase N 收尾，产出 gamma_Phase{N}.dat + NL 曲线 + E_true=f(E_rec)。
#
# run 选择（与 nlfit/src/aggregate.py::select_phase_runs 同口径）：
#   phase 区间    ValProd26BPhase.csv（P1 9737-11045 / P2 11049-12135 /
#                 P3 12136-13463 / P4 13466-15250）
#   中心 run      CalibRUN_from_file.csv 里 |z| <= 0.5 m
#   P1 折叠       区间前的 2025-08 试运行周并入 P1（生产口径；NO_FOLD_PRE=1 关）
#   AmC           该 phase 全部中心 run（nlfit 加权平均需要逐 run 结果）
#   γ 单能源      该 phase 全部中心 run；K40 不入 7 峰表，默认跳过
#
# 连续谱：按设计用已有输入 —— dybmodel_data 里同事交付的
#   Isotope_data_Phase{N}_FVcutR0_1720_Finalcorrection.root
# （nlfit sandbox 内物化到 C++ 固定路径，零改动）。
#
# Usage:
#   bash run_phase_all.sh                 # 全部 4 个 phase 串行
#   bash run_phase_all.sh 2               # 只跑 phase 2
#   bash run_phase_all.sh 1 3             # phase 1 和 3
#   NC_PIN=1 bash run_phase_all.sh        # nC 钉生产值 5.08140（对齐生产口径）
#   NO_FOLD_PRE=1 bash run_phase_all.sh 1 # P1 不折叠 8 月试运行周
#
# 环境变量：
#   DYBMODEL_DATA   dybmodel 数据目录（lustrefs 文件数配额紧时放 scratchfs2）
#   NLFIT_FLAGS     附加 nlfit 参数（如 "--skip-dybmodel" 干跑验证）
#   SUITE_FLAGS     附加顶层 run_pipeline.sh 参数（如 --skip-qa）
#
# 输出：output/<ts>/phase{N}/...  每 phase 一棵完整留档树（suite log +
#   calibsel / calibsel_amc / peakfit / peakfit_amc / nlfit 全套）。
# =============================================================================
set -e
set -o pipefail   # run_pipeline.sh | tee 的失败必须透传（批量作业看 exit code）
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ROOT_TS：并行作业共写一棵树（output/<ROOT_TS>/phase{1..4}）；缺省现取时间戳
TS="${ROOT_TS:-$(date +%Y%m%d_%H%M%S)}"
ROOT_OUT="$SUITE/output/$TS"
CALIB_CSV="$SUITE/runcheck/data/CalibRUN_from_file.csv"
PHASE_CSV="$SUITE/calibsel/input/correction/data/ValProd26BPhase.csv"

ALL_PHASES=("$@")
[ ${#ALL_PHASES[@]} -eq 0 ] && ALL_PHASES=(1 2 3 4)

# ---------- run 解析（python3 stdlib；口径 = select_phase_runs） ----------
# stdout 两行：γ 单能源 "Src=run+run,..."；AmC "run run ..."
phase_centre_runs() {
    python3 - "$1" "$([ -z "${NO_FOLD_PRE:-}" ] && echo 1 || echo 0)" \
            "$CALIB_CSV" "$PHASE_CSV" <<'PY'
import csv, sys
phase, fold_pre = int(sys.argv[1]), sys.argv[2] == "1"
runs = []
with open(sys.argv[3], newline="") as fh:
    for r in csv.DictReader(fh):
        runs.append((int(r["RUN"]), r["Source"], abs(float(r["Z[m]"])) <= 0.5))
ranges = []
with open(sys.argv[4], newline="") as fh:
    for row in csv.DictReader(fh):
        name = next(v for v in row.values() if v and v.strip())
        lo, hi = (int(x) for x in row["Run Range"].split("-"))
        ranges.append((int(name.split()[-1]), lo, hi))
ranges.sort()
match = [r for r in ranges if r[0] == phase]
if not match:
    sys.exit(f"phase {phase} not in phase table")
_lo, lo, hi = match[0]
first_lo = ranges[0][1]
gamma, amc = {}, []
for run, src, centre in runs:
    inside = lo <= run <= hi
    if not inside and phase == 1 and fold_pre and run < first_lo:
        inside = True  # pre-P1 commissioning week folded into Phase 1
    if not (inside and centre):
        continue
    if "Am" in src or "Cf" in src:
        amc.append(run)
    elif src != "K40":          # K40 不入 7 峰表，默认不跑
        gamma.setdefault(src, []).append(run)
print(",".join(f"{s}={'+'.join(map(str, v))}" for s, v in sorted(gamma.items())))
print(" ".join(map(str, sorted(set(amc)))))
PY
}

mkdir -p "$ROOT_OUT"
echo "[phase-driver] output root: $ROOT_OUT"
FAILED=()

for PH in "${ALL_PHASES[@]}"; do
    PH_OUT="$ROOT_OUT/phase$PH"
    echo ""
    echo "###########################################################"
    echo "#  Phase $PH  →  $PH_OUT"
    echo "###########################################################"
    RUNS_FILE="$ROOT_OUT/.runs_phase$PH.txt"
    if ! phase_centre_runs "$PH" > "$RUNS_FILE"; then
        echo "[phase-driver] ERROR: run resolution failed: $(cat "$RUNS_FILE")"
        FAILED+=("$PH"); continue
    fi
    GAMMA_SPEC=$(head -1 "$RUNS_FILE")   # "Ge68=12370+...,Cs137=12295,..."
    read -ra AMC_BARE <<< "$(tail -1 "$RUNS_FILE")"   # 裸 run 号数组
    rm -f "$RUNS_FILE"
    echo "[phase-driver] γ   centre runs: ${GAMMA_SPEC:-<none>}"
    echo "[phase-driver] AmC centre runs: ${AMC_BARE[*]:-<none>}"

    # "Src=run+run" → 裸 run 列表（顶层脚本按裸 run 号路由分流）
    read -ra GAMMA_BARE <<< "$(echo "$GAMMA_SPEC" | tr ',+' '  ' | sed 's/[0-9A-Za-z]*=//g')"
    ALL_RUNS=(${GAMMA_BARE[@]} ${AMC_BARE[@]})
    if [ ${#ALL_RUNS[@]} -eq 0 ]; then
        echo "[phase-driver] ERROR: phase $PH has no centre runs"; FAILED+=("$PH"); continue
    fi
    echo "[phase-driver] front-end runs: ${ALL_RUNS[*]}"

    # 注入 phase 上下文，顶层脚本完成其余一切：
    #   PEAKFIT_RUNS  → peakfit γ 段 --runs（只拟合本 phase 的 run）
    #   NLFIT_PHASE   → nlfit --phase N（聚合表 + per-phase isotope root）
    if ( cd "$SUITE" &&
         export PEAKFIT_RUNS="$GAMMA_SPEC" NLFIT_PHASE="$PH" OUT_ROOT="$PH_OUT"
         [ -n "$NC_PIN" ] && export NLFIT_NC_PIN=1
         bash run_pipeline.sh "${ALL_RUNS[@]}" ${SUITE_FLAGS:-} \
             2>&1 | tee "$ROOT_OUT/phase${PH}_console.log"
       ); then
        echo "[phase-driver] phase $PH OK → $PH_OUT"
    else
        echo "[phase-driver] ERROR: phase $PH FAILED (see $ROOT_OUT/phase${PH}_console.log)"
        FAILED+=("$PH")
    fi
done

echo ""
echo "###########################################################"
if [ ${#FAILED[@]} -eq 0 ]; then
    echo "[phase-driver] all requested phases OK: ${ALL_PHASES[*]}"
    echo "[phase-driver] output root: $ROOT_OUT"
    exit 0
else
    echo "[phase-driver] FAILED phases: ${FAILED[*]}  (root: $ROOT_OUT)"
    exit 1
fi
