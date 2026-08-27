#!/bin/bash
# Create the nlfit virtualenv (pure Python: numpy/scipy/matplotlib only).
# The Stage-6 dybmodel wrap additionally uses the external cvmfs ROOT env
# (config/paths.py :: CVMFS_SETUP) — nothing to install for it.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
.venv/bin/python -c "import numpy, scipy, matplotlib; print('nlfit venv OK')"
