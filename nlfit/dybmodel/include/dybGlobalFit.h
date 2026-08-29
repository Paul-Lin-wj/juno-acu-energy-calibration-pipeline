#ifndef dybGlobalFit_h
#define dybGlobalFit_h

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
#include "TRandom3.h"
#include "TH1F.h"
#include "TLegend.h"
#include "TMinuit.h"
#include "TMath.h"
#include "TString.h"
#include "TGraph.h"
#include "TLegendEntry.h"
#include "TGraphErrors.h"

#include "dybParameters.h"
#include "dybEnergyModel.h"
#include "dybGammaData.h"
#include "dybSpectrum.h"
#include "dybB12Data.h"
#include "dybC11Data.h"
#include "dybC10Data.h"
#include "dybK40Data.h"
#include "dybBi212Data.h"
#include "dybBi214Data.h"
#include "dybTl208Data.h"
#include "dybLSData.h"
#include "dybFadcData.h"
#include "dybAlphaData.h"
#include "dybMichel.h"
#include "dybMichelData.h"

using namespace std;

class dybParameters;

class dybGlobalFit
{
  public:
    dybGlobalFit ();
   ~dybGlobalFit ();
    void          LoadData ();
    void          LoadToyMC(int i=0);
    void          GenToyMC ();
    void          Fit      ();
    void          WriteResult();
    void          Scan     ();
    void          Plot     ();
    void          LoadResult(string name);
    void          SetError (int parNo,int sign);
    void          DrawErrors   ();
    void          GetCLSample  ();
    void          SetContourNItr(int nItr){m_contourNItr=nItr;}
    
    static void   SetParameters();
    static void   SetParameters(Double_t *par);
    static void   SetFreePar(Double_t *par);
    //static void   SetFreePar(Double_t A, Double_t kB, Double_t kC, Double_t alpha, Double_t tau);
    static void   SetParameter(Int_t ipar, Double_t value);
    static double GetChi2      (double maxChi2=-1);
    static double GetReducedChi2();
   
    static double Getm_chi2Min() {return m_chi2Min;}
 
    static dybGammaData *m_gammaData;
    static dybB12Data   *m_b12Data;
    static dybC11Data   *m_c11Data;
    static dybC10Data   *m_c10Data;
    static dybK40Data   *m_k40Data;
    static dybBi212Data *m_bi212Data;
    static dybBi214Data *m_bi214Data;
    static dybTl208Data *m_tl208Data;
    static dybLSData    *m_lsDataLBNL;
    static dybLSData    *m_lsDataIHEP;
    static dybFadcData  *m_fadcData;
    static dybMichel*m_michelData;
    static dybAlphaData *m_alphaData;
    
    static int    m_contourNItr;
    
  private:
    
    double GetDeltaChi2();
    static TRandom3 m_rand;
    static void ChisqFCN(Int_t &npar, Double_t *grad, Double_t &fval, Double_t *par, Int_t flag);
    static TMinuit* m_minuit;
    static int  m_printLevel;

    static double m_parameters[13];
    static int    m_nParameter;
    static int    m_nFreeParameter;
    static int    m_nFitParameter;
    
    static double m_chi2;
    static double m_chi2B12;
    static double m_chi2C11;
    static double m_chi2C10;
    static double m_chi2K40;
    static double m_chi2Bi212;
    static double m_chi2Bi214;
    static double m_chi2Tl208;
    static double m_chi2Gamma;
    static double m_chi2LsLBNL;
    static double m_chi2LsIHEP;
    static double m_chi2Fadc;
    static double m_chi2Michel;
    static double m_chi2Alpha;
    
    static double m_chi2Min;
    static double m_chi2MinRed;
    
    static double m_bestFit     [13];
    static double m_bestFitError[13];
    static double m_covMatrix   [13][13];
    
    vector<double> m_bestFitNL    ;
    vector<double> m_bestFitNLHigh;
    vector<double> m_bestFitNLLow ;
};

#endif
