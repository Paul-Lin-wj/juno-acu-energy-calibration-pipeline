#!/bin/bash
source /cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/Release/J17v1r1/setup.sh
cd /lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP
root -l -b -q 'test_theo_read.C("forNLfitter/12B_pure_beta_0_20MeV_80bins.root")'
