#!/bin/bash
# =============================================================================
# setup_container.sh — FALLBACK: stage a local dybmodel SL6 runtime
# =============================================================================
# NOT NEEDED on nodes mounting /cvmfs/container.ihep.ac.cn — there the
# pipeline uses the official image directly (hep_container exec SL6 -g juno,
# zero copies). Run this ONLY on nodes without that cvmfs repo.
#
# Produces, under $DEST (default: $DYBMODEL_CONTAINER if set; else
# /datafs/users/wujxy/containers/dybmodel-sl6 when /datafs exists; else
# ~/dybmodel-sl6 — e.g. on lustrefs-only nodes; ~18 GB total):
#
#   sl69worknode20240820.sif   byte-identical copy of the official IHEP SL6
#                              worknode image (provenance; def + sha256 in
#                              nlfit/container/)
#   rootfs/                    unsquashfs extraction of the SIF — the
#                              apptainer sandbox used at runtime (this node
#                              has no setuid starter, so userns + dir sandbox)
#   juno-sl6-amd64_gcc447/     J17v1r1 (ROOT 5.34.11 era). Its TEXT setup
#                              scripts get the hardcoded
#                              /cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/...
#                              prefix rewritten to this directory; binaries
#                              are untouched. Staged OUTSIDE /cvmfs because
#                              on this node family /cvmfs/juno.ihep.ac.cn is
#                              a publicfs stand-in without sl6 content and
#                              unprivileged containers cannot shadow
#                              inherited mounts; also avoid directories named
#                              like cvmfs repos (they get auto-mounted over).
#
# NOTE the SIF cannot be rebuilt from the in-repo def: the official image is
# CHAIN-built (localimage layers, no from-scratch recipe — see
# container/sl69worknode20240820.def). Reproducibility = sha256-verified
# byte copy, checked below against container/SHA256SUMS.
#
# Prerequisite: ssh access to a login node mounting container.ihep.ac.cn
# (default lidian@lxlogin002.ihep.ac.cn; override as $1).
# =============================================================================
set -euo pipefail

NODE="${1:-lidian@lxlogin002.ihep.ac.cn}"
if [ -n "${DYBMODEL_CONTAINER:-}" ]; then
    DEST="$DYBMODEL_CONTAINER"
elif [ -d /datafs ]; then
    DEST="/datafs/users/wujxy/containers/dybmodel-sl6"
else
    DEST="$HOME/dybmodel-sl6"
fi
SIF_NAME="sl69worknode20240820.sif"
SIF_SRC="/cvmfs/container.ihep.ac.cn/singularity/image/SL69/$SIF_NAME"
J17_REMOTE="/cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/Release/J17v1r1/"
J17_LOCAL="$DEST/juno-sl6-amd64-gcc447/Release/J17v1r1"
CVMFS_PREFIX="/cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/Release/J17v1r1"

mkdir -p "$DEST" "$J17_LOCAL"

echo "== [1/4] SL6 worknode image (3.6 GB) =="
if [ ! -s "$DEST/$SIF_NAME" ]; then
    ssh "$NODE" "cat $SIF_SRC" > "$DEST/$SIF_NAME"
fi
# behaviour-lock check: must equal nlfit/container/SHA256SUMS
SIF_SHA_EXPECT="$(dirname "$0")/../container/SHA256SUMS"
SIF_SHA_WANT="$(awk '{print $1}' "$SIF_SHA_EXPECT")"
echo "$SIF_SHA_WANT  $DEST/$SIF_NAME" | sha256sum -c - || {
    echo "ERROR: SIF sha256 mismatch vs container/SHA256SUMS"; exit 1; }

echo "== [2/4] J17v1r1 release (3.0 GB) =="
# known harmless gaps: 11 Geant4 PhotonEvaporation files are unreadable for
# the copying account (cvmfs permissions) and unused by the fitter — hence
# `|| true` on the rsync (code 23 would otherwise abort under set -e)
rsync -a --info=stats2 -e ssh "$NODE:$J17_REMOTE" "$J17_LOCAL/" || true

echo "== [3/4] rewrite hardcoded /cvmfs paths in TEXT scripts =="
( cd "$J17_LOCAL"
  grep -rlI "$CVMFS_PREFIX" . | while read -r f; do
      sed -i "s|$CVMFS_PREFIX|$J17_LOCAL|g" "$f"
  done
  remaining=$(grep -rl "$CVMFS_PREFIX" . | wc -l)
  echo "  remaining references: $remaining (expect 0 in text; binaries may keep harmless rpath strings)"
)

echo "== [4/4] extract SIF to rootfs sandbox =="
rm -rf "$DEST/rootfs"
OFFSET=$(apptainer sif list "$DEST/$SIF_NAME" 2>/dev/null | awk '/FS \(Squashfs/ {print $4}' | cut -d- -f1)
[ -n "$OFFSET" ] || { echo "cannot find squashfs offset"; exit 1; }
unsquashfs -q -o "$OFFSET" -d "$DEST/rootfs" "$DEST/$SIF_NAME" \
    > /dev/null 2>&1 || unsquashfs -o "$OFFSET" -d "$DEST/rootfs" "$DEST/$SIF_NAME"
rm -f "$DEST/rootfs/cvmfs/juno.ihep.ac.cn"

( cd "$DEST" && sha256sum "$SIF_NAME" juno-sl6-amd64_gcc447/Release/J17v1r1/setup.sh \
    > ASSETS.sha256 )

echo "Done. Sanity check (expect VERSION=5.34/11):"
DEST_ROOT="$(dirname "$DEST" | while read -r d; do [ "$d" != / ] && echo "$d" && break; done)"
apptainer exec -e --userns -B "$DEST_ROOT:$DEST_ROOT" "$DEST/rootfs" bash -c \
    "export HOME=/root USER=root; source $J17_LOCAL/setup.sh >/dev/null 2>&1; \
     root-config --version"
