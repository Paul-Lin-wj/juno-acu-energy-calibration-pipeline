#!/bin/bash
# =============================================================================
# fetch_dybmodel_data.sh — stage the dybmodel fitter DATA + prebuilt binary
# =============================================================================
# The C++ source is vendored in-repo (nlfit/dybmodel/, byte-verified against
# ENL_FITTER_COMMIT in config/paths.py), and the RUNTIME data set ships with
# the repo too: small files in plain git, Quenching.root + the prebuilt
# `fitter` binary via Git LFS (.gitattributes).
#
# This script is now the FULL-TREE / repair path: it stages the complete
# 773 MB necessaryfiles/ (including the ~409 MB Spec/ build-time area that
# git excludes) into $DYBMODEL_DATA (default nlfit/dybmodel_data/). Use it
# when a clone was made without LFS, when the runtime set is incomplete, or
# when you need the build-time spectra.
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
check_pin() {  # $1 expected  $2 file  $3 label
    if echo "$1  $2" | sha256sum -c - >/dev/null 2>&1; then
        echo "[fetch]   $3: sha256 OK"
        return 0
    fi
    echo "[fetch]   $3: sha256 MISMATCH (expected ${1:0:16}..., got $(sha256sum "$2" 2>/dev/null | cut -c1-16)...)"
    return 1
}
rc=0
check_pin "$BIN_SHA" "$DEST/fitter" "fitter binary" || rc=1
check_pin "$QC_SHA" "$QC" "Quenching.root" || rc=1
if [ "$rc" -ne 0 ]; then
    cat <<'EOF'
[fetch] The source you fetched from is NOT the pinned upstream
        (wujxy/ENL_fitter @ the commit in config/paths.py).
        This is expected when using an alternative source (e.g. a
        zhaorz@lustrefs copy). The behaviour lock is then NOT guaranteed
        by provenance — you MUST establish it empirically:
          1) run nlfit with --validate-ref on a known-good gamma table,
          2) confirm the bestFit comparison passes before trusting physics.
        To accept the mismatch deliberately:  ALLOW_MISMATCH=1 <re-run fetch>
EOF
    if [ "${ALLOW_MISMATCH:-0}" != "1" ]; then
        exit 1
    fi
    echo "[fetch] ALLOW_MISMATCH=1 — continuing with unpinned source."
fi
[ -n "$TMPCLONE" ] && rm -rf "$(dirname "$TMPCLONE")"
echo "[fetch] done. Set DYBMODEL_DATA=$DEST (default already) and run nlfit."
