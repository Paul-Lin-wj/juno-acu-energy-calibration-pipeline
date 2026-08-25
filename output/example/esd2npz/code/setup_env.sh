#!/bin/bash
# setup_env.sh — create .venv, install dependencies, and fetch the one
# third-party shared library needed by stage 0 (ESD->EDM) on hosts that do
# not ship libpcre.so.1 (EL9 clusters do; newer distros don't).
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if [ ! -d .venv ]; then
    echo "Creating virtual environment .venv ..."
    "$PY" -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# libpcre.so.1 for the ESD->EDM stage (JUNO offline SW links against it).
mkdir -p lib
if ! ldconfig -p 2>/dev/null | grep -q "libpcre.so.1" && [ ! -e lib/libpcre.so.1 ]; then
    echo "libpcre.so.1 not found on this host; copying from CVMFS ..."
    COPIED=0
    for d in \
        /cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202105/lib \
        /cvmfs/common.ihep.ac.cn/software/anaconda/anaconda3-202002/lib
    do
        if [ -e "$d/libpcre.so.1" ]; then
            cp -L "$d/libpcre.so.1" lib/libpcre.so.1
            COPIED=1
            break
        fi
    done
    if [ "$COPIED" -ne 1 ]; then
        echo "WARNING: could not find libpcre.so.1 on CVMFS either."
        echo "         Stage 0 (ESD->EDM) will not work until it is provided in lib/."
    fi
fi

echo ""
echo "Environment ready. Activate with:"
echo "  source .venv/bin/activate"
