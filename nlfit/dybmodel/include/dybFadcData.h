#ifndef dybFadcData_h
#define dybFadcData_h

#include <string>
#include "TF1.h"
#include "dybEnergyModel.h"
#include "dybData.h"

using namespace std;

class dybFadcData: public dybData
{
  public:
    dybFadcData();
   ~dybFadcData();
   
    static double s_fadcNor;
    static double s_fadcRes;
    void   LoadData (string fileName);
    void   LoadToyMC(string fileName);
    void   GenToyMC ();
    double GetChi2  (int nDoF = 0);
    TGraphErrors Plot(bool writeToFile=false);
    TGraph fadcResCorr();
  private:
    const static int nDataMax    = 50;
    const static int nEnergyMax = 100;
    //int    m_nData;
    //double m_data   [nHitMax];
    double m_energy          [nDataMax];
    double m_adNonlin        [nDataMax];
    double m_adNonlinError   [nDataMax];
    //double m_multPdf[nHitMax][nDataMax];
    //double m_scale;
    TF1* m_fit;
    double FitF(double *x, double *par);
    void ChannelToAD();
};  

#endif
