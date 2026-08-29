#!/bin/bash
set -euo pipefail

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

echo "=== [el9] export histogram sidecars ==="
for f in "${files[@]}"; do
  echo "--- export $f ---"
  root -l -b -q "export_predSpec_sidecar.C(\"$f\")"
done

echo
echo "=== [SL6] convert to forNLfitter ==="
chmod +x run_convert_in_sl6.sh
/cvmfs/container.ihep.ac.cn/bin/hep_container exec SL6 -g dyw bash "$DIR/run_convert_in_sl6.sh"
