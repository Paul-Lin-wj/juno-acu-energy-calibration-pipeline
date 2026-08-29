#ifndef dybMichel_h
#define dybMichel_h

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <math.h>
#include <unistd.h>
#include "TFile.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TMath.h"
#include "TString.h"
#include "TLegend.h"
#include "TLegendEntry.h"
#include "TGraph.h"
#include "TGraphErrors.h"
#include "dybEnergyModel.h"
#include "dybData.h"

using namespace std;

class dybMichel: public dybData
{
  public:
    dybMichel();
    
    void   LoadData (string fileName);
    double GetChi2  (int nDoF = 0);
    void   GenToyMC ();
    
    TGraphErrors Plot(bool writeToFile=false);
  private:
    double m_data;
    double m_dataE;
    double m_michelEnergy;
};

#endif
