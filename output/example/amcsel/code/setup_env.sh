#!/usr/bin/env bash
# amcsel 环境布防：python3 -m venv .venv + requirements
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python -c "import numpy, pandas, matplotlib, scienceplots, iminuit, awkward, numba; print('amcsel env ready')"
