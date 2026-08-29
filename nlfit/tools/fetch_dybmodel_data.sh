#!/bin/bash
# =============================================================================
# fetch_dybmodel_data.sh — stage the dybmodel fitter DATA + prebuilt binary
# =============================================================================
# The C++ source is vendored in-repo (nlfit/dybmodel/, byte-verified against
# ENL_FITTER_COMMIT in config/paths.py). Everything too big for git — the
# 773 MB necessaryfiles/ tree and the prebuilt 1.4 MB `fitter` binary — is
# staged by this script into $DYBMODEL_DATA (default nlfit/dybmodel_data/,
# gitignored).
#
# Sources, in order (override with env):
#   DYBMODEL_FROM  a ready local checkout of ENL_fitter at the pinned commit
#                  (default: /datafs/users/wujxy/agent-sci/ENL_agent/
#                   fitter_energynl_dybmodel — this machine's copy)
#   ENL_FITTER_URL a git URL of the upstream mirror (e.g.
#                  git@github.com:wujxy/ENL_fitter.git) used when the local
#                  path is absent: cloned to a temp dir, checked out at the
#                  pinned commit, then copied from there.
#
# Quenching.root (364 MB) is NOT in the upstream HEAD tree: if missing it is
# recovered from the old commit recorded in QUENCHING_RECOVER_COMMIT
# (config/paths.py) inside the source checkout.
#
# Verification: sha256 of the binary and Quenching.root against the pins in
# config/paths.py; the necessaryfiles tree is trusted from the pinned commit.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
[ -f "$HERE/.venv/bin/python" ] && source "$HERE/.venv/bin/activate"

DEST="${DYBMODEL_DATA:-$HERE/dybmodel_data}"
FROM="${DYBMODEL_FROM:-/datafs/users/wujxy/agent-sci/ENL_agent/fitter_energynl_dybmodel}"
COMMIT="$(python3 -c "import sys; sys.path.insert(0,'$HERE/config'); import paths as P; print(P.ENL_FITTER_COMMIT)")"
QC_COMMIT="$(python3 -c "import sys; sys.path.insert(0,'$HERE/config'); import paths as P; print(P.QUENCHING_RECOVER_COMMIT)")"
BIN_SHA="$(python3 -c "import sys; sys.path.insert(0,'$HERE/config'); import paths as P; print(P.DYBMODEL_BIN_SHA256)")"
QC_SHA="$(python3 -c "import sys; sys.path.insert(0,'$HERE/config'); import paths as P; print(P.QUENCHING_SHA256)")"

TMPCLONE=""
if [ ! -d "$FROM/necessaryfiles" ]; then
    URL="${ENL_FITTER_URL:-git@github.com:wujxy/ENL_fitter.git}"
    echo "[fetch] local source $FROM not found — cloning $URL @ $COMMIT"
    TMPCLONE="$(mktemp -d)/enl_fitter"
    git clone "$URL" "$TMPCLONE"
    git -C "$TMPCLONE" checkout "$COMMIT"
    FROM="$TMPCLONE"
fi
echo "[fetch] source : $FROM"
echo "[fetch] dest   : $DEST"

mkdir -p "$DEST"
echo "[fetch] 1/3  necessaryfiles/ (rsync, ~773 MB)"
rsync -a "$FROM/necessaryfiles/" "$DEST/necessaryfiles/"

echo "[fetch] 2/3  Quenching.root"
QC="$DEST/necessaryfiles/input/Quenching.root"
if [ ! -f "$QC" ]; then
    echo "[fetch]   recovering from old commit $QC_COMMIT (not in HEAD)"
    mkdir -p "$(dirname "$QC")"
    git -C "$FROM" show "$QC_COMMIT:necessaryfiles/input/Quenching.root" > "$QC"
fi

echo "[fetch] 3/3  prebuilt fitter binary"
cp -f "$FROM/fitter" "$DEST/fitter"

echo "[fetch] verifying sha256 pins ..."
echo "$BIN_SHA  $DEST/fitter" | sha256sum -c -
echo "$QC_SHA  $QC" | sha256sum -c -
[ -n "$TMPCLONE" ] && rm -rf "$(dirname "$TMPCLONE")"
echo "[fetch] done. Set DYBMODEL_DATA=$DEST (default already) and run nlfit."
