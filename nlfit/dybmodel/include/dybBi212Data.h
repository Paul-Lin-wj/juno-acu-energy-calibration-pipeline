#ifndef dybBi212Data_h
#define dybBi212Data_h

#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <math.h>
#include <dirent.h>
#include <unistd.h>
#include "TTree.h"
#include "TFile.h"
#include "TChain.h"
#include "TCanvas.h"
#include "TPad.h"
#include "TRandom3.h"
#include "TH1F.h"
#include "TMath.h"
#include "TString.h"
#include "TLegend.h"
#include "TLegendEntry.h"
#include "TGraph.h"
#include "TGraphErrors.h"

#include "dybParameters.h"
#include "dybEnergyModel.h"
#include "dybData.h"
#include "dybGammaPeak.h"
#include "dybSpectrum.h"

using namespace std;

class dybBi212Data: public dybSpectrum
{
  public:
    dybBi212Data() : dybSpectrum(s_nMaxBins,
                                 s_nMaxBinsData,
                                 s_nMaxBr,
                                 s_nMaxGam){;}
    void  SetParameters();
    void  InitTheo     ();
    void  InitData     (string fileName);
    
  private:
    static unsigned int s_nMaxBr;
    static unsigned int s_nMaxGam;
    static unsigned int s_nMaxBins;
    static unsigned int s_nMaxBinsData;
};
#endif
