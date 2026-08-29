#ifndef fitNLCurve_h
#define fitNLCurve_h

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
#include "TGraph.h"
#include "TGraphErrors.h"
#include "TRandom3.h"
#include "dybEnergyModel.h"
#include "dybData.h"

using namespace std;

class fitNLCurve: public dybData
{
  public:
    fitNLCurve(string groupName);
   ~fitNLCurve();
    
    void   LoadData (string fileName);
    double GetChi2  (int nDoF = 0);
    void   GenToyMC ();
    
    TGraphErrors Plot(bool writeToFile=false);
  private:
    //int          m_nData;
    string       m_groupName;
    double       m_scale;
    TGraphErrors m_data;
    TF1*         m_fit;
    double FitF(double *x, double *par);
};

#endif
