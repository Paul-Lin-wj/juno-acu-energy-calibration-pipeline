#ifndef dybAlphaData_h
#define dybAlphaData_h

#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <math.h>
#include "TFile.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TGraph.h"
#include "TGraphErrors.h"
#include "TMultiGraph.h"
#include "TRandom3.h"
#include "TLegend.h"
#include "TLegendEntry.h"
#include "TLatex.h"
#include "dybEnergyModel.h"
#include "dybData.h"
#include "dybAlphaPeak.h"
#include "dybFadcData.h"

//class dybParameters;

class dybAlphaData: public dybData
{
  public:
    dybAlphaData();
    void         LoadData(string fileName);
    double       GetChi2 (int nDoF = 0);
    void         GenToyMC();
    
    void Plot(bool writeToFile);
    
    TGraphErrors PlotDataScintNL(){return PlotPeaks(1);}
    TGraphErrors PlotDataFullNL (){return PlotPeaks(2);}
    TGraphErrors PlotTheoScintNL(){return PlotPeaks(3);}
    TGraphErrors PlotTheoFullNL (){return PlotPeaks(4);}
    
  private:
    vector<dybAlphaPeak> m_data;
    TGraphErrors PlotPeaks(int type);
    void AddPeak(string name,double eTru);
};
  
#endif
