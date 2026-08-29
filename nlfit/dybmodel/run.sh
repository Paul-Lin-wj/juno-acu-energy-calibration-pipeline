#!/bin/bash
source /cvmfs/juno.ihep.ac.cn/sl6_amd64_gcc447/Release/J17v1r1/setup.sh 

g++ --version
make clean

make
#./pullcurve  
./fitter
