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
#   ├── suite_run_log.{md,json}  # THIS run: argv/env/stage table/module audits
#   ├── suite_console.log        # full driver console (tee'd)
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
# Requires the submodules' venvs to exist (auto-created on first use).
#
# Every figure produced anywhere in the chain ends up with a PNG twin (screen
# viewing) and a PDF twin (slides/print): ported ROOT/matplotlib code is left
# untouched; a final pairing pass mirrors whichever side is missing.

set -e
SUITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$SUITE/output/$TS"
mkdir -p "$OUT/recon" "$OUT/calibsel" "$OUT/calibsel_amc" "$OUT/peakfit" "$OUT/peakfit_amc" "$OUT/nlfit"

# ---------------- suite-level bookkeeping ----------------
# Console tee: everything below also lands in $OUT/suite_console.log.
exec > >(tee -a "$OUT/suite_console.log") 2>&1

SUITE_START=$(date +%s)
CURRENT_STAGE="init"
STAGES_TMP="$OUT/.suite_stages.tmp"
: > "$STAGES_TMP"

# run_stage "<label>" <cmd...>  — run a stage, record label/rc/seconds.
# The stage runs in a SUBSHELL: set -e keeps working inside the stage body
# (a `"$@" || rc=$?` without the subshell would suppress set -e for the whole
# function and silently swallow mid-stage failures). Stages therefore must
# NOT pass state via globals — later stages derive inputs from the output
# tree instead (which also makes re-running individual stages safe).
run_stage() {
    local label="$1"; shift
    CURRENT_STAGE="$label"
    echo ""
    echo "=== $label ==="
    local t0 rc=0
    t0=$(date +%s)
    ( "$@" ) || rc=$?
    printf '%s\t%s\t%s\n' "$label" "$rc" "$(( $(date +%s) - t0 ))" >> "$STAGES_TMP"
    [ "$rc" -eq 0 ] && CURRENT_STAGE="idle"   # keep the label on failure
    return "$rc"
}

# write_suite_log <final_rc> — called from the EXIT trap in ALL cases
# (success, stage failure, Ctrl-C), so a suite_run_log always exists.
write_suite_log() {
    local final_rc="$1"
    set +e
    SUITELOG_RC="$final_rc" \
    SUITELOG_STAGE="$CURRENT_STAGE" \
    SUITELOG_OUT="$OUT" SUITELOG_SUITE="$SUITE" SUITELOG_START="$SUITE_START" \
    SUITELOG_GAMMA="${GAMMA_RUNS[*]:-}" SUITELOG_AMC="${AMC_RUNS[*]:-}" \
    SUITELOG_ENV_RUNS="${RUNS_ENV:-}" SUITELOG_ENV_AMC="${AMC_RUNS_ENV_STR:-}" \
    SUITELOG_DEFAULT_AMC="${DEFAULT_AMC_RUN-10110}" \
    SUITELOG_RECON_IMPL="${RECON_IMPL:-}" SUITELOG_RECON_SLICE="${RECON_SLICE:-1}" \
    SUITELOG_RECON_EVTMAX="${RECON_EVTMAX:-100}" SUITELOG_NLFIT_FLAGS="${NLFIT_FLAGS:-}" \
    SUITELOG_STAGES_TMP="$STAGES_TMP" \
    python3 - <<'PY' || echo "[suite-log] WARNING: suite_run_log writer FAILED (see above)"
import json, os, socket, subprocess, time
from pathlib import Path

out = Path(os.environ["SUITELOG_OUT"])
suite = Path(os.environ["SUITELOG_SUITE"])
start = int(os.environ["SUITELOG_START"])
rc = int(os.environ["SUITELOG_RC"])

stages = []
tmp = Path(os.environ["SUITELOG_STAGES_TMP"])
if tmp.exists():
    for line in tmp.read_text().splitlines():
        label, src, secs = line.split("\t")
        stages.append({"stage": label, "exit_code": int(src),
                       "elapsed_s": int(secs),
                       "status": "ok" if int(src) == 0 else "FAILED"})

def git_info():
    def g(*a):
        try:
            return subprocess.run(["git", "-C", str(suite), *a],
                                  capture_output=True, text=True, timeout=10
                                  ).stdout.strip()
        except Exception:
            return ""
    return {"commit": g("rev-parse", "HEAD") or "unknown",
            "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(g("status", "--porcelain"))}

modules = {}
for m in ("recon", "calibsel", "calibsel_amc", "peakfit", "peakfit_amc", "nlfit"):
    rl = out / m / "run_log.json"
    if rl.exists():
        try:
            d = json.loads(rl.read_text())
            modules[m] = {"status": d.get("status"),
                          "audit_passed": (d.get("audit") or {}).get("passed")}
        except Exception as e:
            modules[m] = {"status": f"unreadable ({e})"}

def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(epoch))

log = {
    "suite": "juno-acu-energy-calibration-pipeline",
    "started": iso(start), "finished": iso(time.time()),
    "elapsed_s": int(time.time()) - start,
    "host": socket.gethostname(), "user": os.environ.get("USER", ""),
    "git": git_info(),
    "exit_code": rc,
    "status": "completed" if rc == 0
              else f"failed during: {os.environ['SUITELOG_STAGE']}",
    "config": {
        "env_runs": os.environ.get("SUITELOG_ENV_RUNS", ""),
        "env_amc_runs": os.environ.get("SUITELOG_ENV_AMC", ""),
        "default_amc_run": os.environ.get("SUITELOG_DEFAULT_AMC", ""),
        "recon": {"impl": os.environ.get("SUITELOG_RECON_IMPL", ""),
                  "slice": os.environ.get("SUITELOG_RECON_SLICE", ""),
                  "evtmax": os.environ.get("SUITELOG_RECON_EVTMAX", "")},
        "nlfit_flags": os.environ.get("SUITELOG_NLFIT_FLAGS", ""),
        "resolved_gamma_runs": os.environ.get("SUITELOG_GAMMA", ""),
        "resolved_amc_runs": os.environ.get("SUITELOG_AMC", ""),
    },
    "stages": stages,
    "modules": modules,
    "output_root": str(out),
}
(out / "suite_run_log.json").write_text(
    json.dumps(log, indent=2, ensure_ascii=False))

md = (["# Suite run log", "",
       f"- started: {log['started']}  finished: {log['finished']}"
       f"  ({log['elapsed_s']} s)",
       f"- status: **{log['status']}** (exit {rc})",
       f"- host: {log['host']}   user: {log['user']}",
       f"- git: {log['git']['commit'][:12]}"
       f"{' (dirty)' if log['git']['dirty'] else ''}", "",
       "## Stages", "",
       "| stage | status | elapsed (s) |", "| --- | --- | --- |"]
      + [f"| {s['stage']} | {s['status']} | {s['elapsed_s']} |" for s in stages]
      + ["", "## Module run logs / audits", "",
         "| module | status | audit passed |", "| --- | --- | --- |"]
      + [f"| {m} | {v['status']} | {v.get('audit_passed')} |"
         for m, v in modules.items()]
      + ["", f"- output root: `{out}`"])
(out / "suite_run_log.md").write_text("\n".join(md) + "\n")
PY
    rm -f "$STAGES_TMP"
}
trap 'rc=$?; trap - EXIT; write_suite_log "$rc"' EXIT

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
classify() {  # echo "AmC" or "gamma" for a run id (stdlib-only, no venv needed)
    command -v python3 >/dev/null 2>&1 || {
        echo "ERROR: python3 not found — cannot classify run $1"; return 1; }
    python3 - "$1" "$CALIB_INFO" <<'PY'
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
    src="$(classify "$r" 2>/dev/null)" || true
    if [ -z "$src" ]; then
        echo "[Warning] run $r not found in calib_to_analyze.txt — routing to gamma branch"
        src="gamma"
    fi
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

# ---------------- stage functions ----------------

stage_recon() {
    # RECON_IMPL=omilrecv2|baseline 开启本地重建（默认关闭 = 用生产 ESD）。
    # 产物 ESD 清单（$OUT/recon/results/esd_lists）由 γ 分支按存在性自动衔接。
    if [ -n "${RECON_IMPL:-}" ]; then
        RECON_RUNS=(${GAMMA_RUNS[@]} ${AMC_RUNS[@]})
        if [ ${#RECON_RUNS[@]} -gt 0 ]; then
            echo "recon ($RECON_IMPL): rtraw → ESD → $OUT/recon"
            cd "$SUITE/recon"
            bash run_pipeline.sh "${RECON_RUNS[@]}" --impl "$RECON_IMPL" \
                --slice "${RECON_SLICE:-1}" --evtmax "${RECON_EVTMAX:-100}" \
                --out-dir "$OUT/recon"
        else
            echo "recon: skipped (no runs given)"
        fi
    else
        echo "recon: skipped (RECON_IMPL unset — using production ESD)"
    fi
}

stage_calibsel_gamma() {
    # （未给 run 时保留 calibsel 自己的 DEFAULT_RUNS 默认；显式只给 AmC run 时跳过）
    if [ ${#GAMMA_RUNS[@]} -gt 0 ] || [ ${#RUNS[@]} -eq 0 ]; then
        echo "calibsel (gamma): EDM → selection NPZ → $OUT/calibsel"
        cd "$SUITE/calibsel"
        CALIBSEL_ARGS=("${GAMMA_RUNS[@]}" "${GAMMA_FLAGS[@]}" --out-dir "$OUT/calibsel")
        # recon 本地重建的 ESD 清单（含 Stage 0；本底 run 需一并重建）
        if [ -n "${RECON_IMPL:-}" ] && [ ${#GAMMA_RUNS[@]} -gt 0 ] \
           && [ -d "$OUT/recon/results/esd_lists" ]; then
            CALIBSEL_ARGS+=(--full-esd --esd-list-dir "$OUT/recon/results/esd_lists")
        fi
        bash run_pipeline.sh "${CALIBSEL_ARGS[@]}"
    else
        echo "calibsel (gamma): skipped (no gamma runs)"
    fi
}

stage_calibsel_amc() {
    if [ ${#AMC_RUNS[@]} -gt 0 ]; then
        echo "calibsel (AmC): correlated pairs → $OUT/calibsel_amc"
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
        done
    else
        echo "calibsel (AmC): skipped (no AmC runs)"
    fi
}

stage_peakfit_gamma() {
    cd "$SUITE/peakfit"
    PY="$SUITE/peakfit/.venv/bin/python"
    [ -x "$PY" ] || { echo "ERROR: peakfit/.venv missing — run peakfit/setup_env.sh first"; return 1; }
    SEL_DIR="$OUT/calibsel/results/selection_npz"
    if compgen -G "$SEL_DIR/*.npz" >/dev/null; then
        "$PY" pipeline/run_fit_all.py --input-dir "$SEL_DIR" \
                                      --out-dir "$OUT/peakfit"
    else
        echo "peakfit (gamma): skipped — no selection NPZ in this batch" \
             "(gamma branch off/unavailable, or calibsel produced nothing)"
    fi
}

stage_peakfit_amc() {
    cd "$SUITE/peakfit"
    PY="$SUITE/peakfit/.venv/bin/python"
    [ -x "$PY" ] || { echo "ERROR: peakfit/.venv missing — run peakfit/setup_env.sh first"; return 1; }
    # 拟合本批产出了 correlation npz 的最后一个 AmC run
    r=""
    for x in "${AMC_RUNS[@]}"; do
        [ -f "$OUT/calibsel_amc/results/RUN$x/correlation_result_RUN$x.npz" ] && r="$x"
    done
    if [ -n "$r" ]; then
        if [ ${#AMC_RUNS[@]} -gt 1 ]; then
            echo "[Warning] ${#AMC_RUNS[@]} AmC runs selected but only run $r" \
                 "is peak-fitted; the others are selection-only."
        fi
        # AmC 拟合单独留档（避免与 γ 拟合的 run_log 互相覆盖），
        # 结果 npz 汇入 $OUT/peakfit/results 供 nlfit 统一消费
        "$PY" pipeline/run_amc_fit_all.py --run "$r" \
            --corr-npz "$OUT/calibsel_amc/results/RUN$r/correlation_result_RUN$r.npz" \
            --out-dir "$OUT/peakfit_amc"
        mkdir -p "$OUT/peakfit/results"
        cp "$OUT"/peakfit_amc/results/RUN"${r}"_*.npz "$OUT/peakfit/results/"
    else
        echo "peakfit (AmC): skipped (no correlation npz from this batch)"
    fi
}

stage_nlfit() {
    cd "$SUITE/nlfit"
    NLFIT_ARGS=(--fitter-results "$OUT/peakfit/results" --out-dir "$OUT/nlfit")
    # extra nlfit flags (e.g. --skip-dybmodel) via env: NLFIT_FLAGS="--skip-dybmodel"
    if [ -n "$NLFIT_FLAGS" ]; then NLFIT_ARGS+=($NLFIT_FLAGS); fi
    bash run_pipeline.sh "${NLFIT_ARGS[@]}"
}

# Pair every figure PNG<->PDF under the batch output (idempotent). Ported
# physics/plot code stays untouched; the pass only mirrors the missing side.
stage_figure_pairs() {
    FIGPY="$SUITE/calibsel/.venv/bin/python"
    [ -x "$FIGPY" ] || FIGPY="$SUITE/peakfit/.venv/bin/python"
    [ -x "$FIGPY" ] || FIGPY="python3"
    "$FIGPY" - "$OUT" <<'PY'
import re
import shutil, subprocess, sys
from pathlib import Path

out = Path(sys.argv[1])
have_pdftoppm = bool(shutil.which("pdftoppm"))
try:
    from PIL import Image
    have_pil = True
except ImportError:
    have_pil = False

for figs in sorted(out.glob("*/figures")) + sorted(out.glob("*/results")):
    for pdf in sorted(figs.rglob("*.pdf")):
        if "/code/" in str(pdf):
            continue
        if pdf.with_suffix(".png").exists():
            continue
        if pdf.with_name(pdf.stem + "-1.png").exists():  # already rasterized
            continue
        if have_pdftoppm:
            subprocess.run(["pdftoppm", "-png", "-r", "150", str(pdf),
                            str(pdf.with_suffix(""))], check=False)
            print(f"[fig-pair] {pdf.name} -> PNG")
        else:
            print(f"[fig-pair] pdftoppm missing, cannot mirror {pdf}")
    for png in sorted(figs.rglob("*.png")):
        if "/code/" in str(png) or re.search(r"-\d+$", png.stem):
            continue  # code snapshot, or a pdftoppm page output (stem-N.png)
        if png.with_suffix(".pdf").exists():
            continue
        if have_pil:
            try:
                img = Image.open(png).convert("RGB")
                img.save(png.with_suffix(".pdf"), "PDF")
                print(f"[fig-pair] {png.name} -> PDF")
            except Exception as e:
                print(f"[fig-pair] {png.name}: {e}")
        else:
            print(f"[fig-pair] PIL missing, cannot mirror {png}")
PY
}

# ---------------- run the chain ----------------
run_stage "[0/6] recon"                 stage_recon
run_stage "[1/6] calibsel (gamma)"      stage_calibsel_gamma
run_stage "[2/6] calibsel (AmC)"        stage_calibsel_amc
run_stage "[3/6] peakfit (gamma)"       stage_peakfit_gamma
run_stage "[4/6] peakfit (AmC)"         stage_peakfit_amc
run_stage "[5/6] nlfit"                 stage_nlfit
run_stage "[5b/6] figure pairs"         stage_figure_pairs

echo ""
echo "=============================================="
echo "Joint run complete."
echo "Suite log   : $OUT/suite_run_log.md"
echo "Output root : $OUT"
echo "  recon       : $OUT/recon       (only if RECON_IMPL set: local rtraw→ESD)"
echo "  calibsel    : $OUT/calibsel    (selection NPZ for peakfit)"
echo "  calibsel_amc: $OUT/calibsel_amc (correlation_result_RUN{N}.npz)"
echo "  peakfit     : $OUT/peakfit     (RUN{N}_{src}.npz incl. nH/nC/AmC + ENL plot)"
echo "  nlfit       : $OUT/nlfit       (gamma_AllPhase.dat + NL curves + E_true lookup)"
echo "=============================================="
