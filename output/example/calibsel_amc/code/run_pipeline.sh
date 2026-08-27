#!/usr/bin/env bash
# amcsel 薄封装 —— 用法：./run_pipeline.sh <RUN> [额外参数传给 pipeline/run_amcsel_all.py]
set -euo pipefail
cd "$(dirname "$0")"
RUN="${1:?usage: run_pipeline.sh <RUN> [extra args...]}"
shift || true
if [ ! -x .venv/bin/python ]; then
    echo "[Info] no .venv found, running setup_env.sh ..."
    bash setup_env.sh
fi
exec .venv/bin/python pipeline/run_amcsel_all.py --run "$RUN" "$@"
