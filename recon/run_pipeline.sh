#!/bin/bash
# =============================================================================
# run_pipeline.sh — recon 模块入口（Stage −1: rtraw → ESD）
#
# 纯编排包装官方 junosw 重建（CVMFS J26.1.1 的 tut_rtraw2rec.py），
# --impl omilrecv2 时叠加优化后的 OMILRECV2 overlay（../omilrec_opt/omilrecv2）。
# 无需 venv：编排脚本仅用标准库，重建在 wrapper 内用 CVMFS python 跑。
#
# Usage:
#   bash run_pipeline.sh                          # 默认 10110, omilrecv2, 1文件×100事例
#   bash run_pipeline.sh 10110 --impl baseline    # CVMFS 官方基线 OMILREC
#   bash run_pipeline.sh 10110 --slice 3 --evtmax 1000
#   bash run_pipeline.sh --out-dir <dir> ...      # 与套件联合跑时指定
# =============================================================================
set -e
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$PROJ/pipeline/run_recon_all.py" "$@"
