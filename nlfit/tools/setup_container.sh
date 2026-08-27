#!/bin/bash
# =============================================================================
# setup_container.sh — stage the dybmodel SL6 runtime onto this machine
# =============================================================================
# Produces, under $DEST (default /datafs/users/wujxy/containers/dybmodel-sl6):
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
# Prerequisite: ssh access to a login node mounting container.ihep.ac.cn
# (default lidian@lxlogin002.ihep.ac.cn; override as $1).
# =============================================================================
set -euo pipefail

NODE="${1:-lidian@lxlogin002.ihep.ac.cn}"
DEST="${DYBMODEL_CONTAINER_DIR:-/datafs/users/wujxy/containers/dybmodel-sl6}"
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
sha256sum "$DEST/$SIF_NAME"

echo "== [2/4] J17v1r1 release (3.0 GB) =="
rsync -a --info=stats2 -e ssh "$NODE:$J17_REMOTE" "$J17_LOCAL/"
# known harmless gaps: 11 Geant4 PhotonEvaporation files are unreadable for
# the copying account (cvmfs permissions) and unused by the fitter

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
apptainer exec -e --userns -B /datafs:/datafs "$DEST/rootfs" bash -c \
    "export HOME=/root USER=root; source $J17_LOCAL/setup.sh >/dev/null 2>&1; \
     root-config --version"
