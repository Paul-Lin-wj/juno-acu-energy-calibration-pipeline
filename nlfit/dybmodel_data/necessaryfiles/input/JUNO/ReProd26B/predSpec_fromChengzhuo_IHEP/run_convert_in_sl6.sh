#!/bin/bash
set -eo pipefail

source /cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/Release/J17v1r1/setup.sh
set -u
DIR="/lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP"
cd "$DIR"

files=(
  "12B_pure_beta_0_20MeV_80bins.root"
  "12N_pure_beta_0_20MeV_80bins.root"
  "10C_pure_beta_0_4MeV_80bins.root"
  "11C_pure_beta_0_4MeV_80bins.root"
  "11Be_pure_beta_0_4MeV_80bins.root"
  "11C_pure_beta_0_4MeV_200bins.root"
)

for f in "${files[@]}"; do
  echo "=== converting $f ==="
  root -l -b -q "convert4NLfitter.C(\"$f\")"
done

echo "=== done ==="
ls -la forNLfitter/
