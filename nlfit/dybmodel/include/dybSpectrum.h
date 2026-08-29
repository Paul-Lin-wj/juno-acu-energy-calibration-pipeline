#ifndef dybSpectrum_h
#define dybSpectrum_h

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
#include "TROOT.h"

#include "dybParameters.h"
#include "dybEnergyModel.h"
#include "dybData.h"
#include "dybLSData.h"
#include "dybGammaPeak.h"

using namespace std;

class dybSpectrum: public dybData
{
  public:
    dybSpectrum(int nMaxBins    ,
                int nMaxBinsData,  
                int nMaxBr      ,
                int nMaxGam     ); 
   ~dybSpectrum();
   
    void   LoadData(string fileName);
    double GetChi2 (int nDoF = 0);
    void   GenToyMC();
    
    TH1F Plot       (bool writeToFile);
    TH1F PlotData   (){return PlotSpec(0);}
    TH1F PlotETru   (){return PlotSpec(1);}
    TH1F PlotEVis   (){return PlotSpec(2);}
    TH1F PlotERec   (){return PlotSpec(3);}
    TH1F PlotERecSig(){return PlotSpec(5);}
    TH1F PlotERecBck(){return PlotSpec(6);}
    TH1F PlotTheo   (){return PlotSpec(10);}
    
    static double s_n12Ratio;
    static double s_c10C11Frac;
    static double s_c10Be11Frac;
    static double s_k40Scale;
    static double s_b12Branch0;
    static double s_b12Branch1;
    static double s_b12Branch2;
    static double s_n12Branch0;
    static double s_n12Branch1;
    static double s_n12Branch2;
    static double s_n12Branch3;
    static double s_n12Branch4;

    static double s_b12branch0WM;
    static double s_b12branch1WM;
    static double s_b12branch2WM;
    static double s_n12branch0WM;
    static double s_n12branch1WM;
    static double s_n12branch2WM;
    static double s_n12branch3WM;
    static double s_n12branch4WM;

    TH1F m_eTruH;
    TH1F m_eVisH;
    TH1F m_eSmrH;
    TH1F m_eRecH;
    
  protected:
    /// dybSpectrum bin number        
    /// number of decay branches		  
	unsigned int m_nBins;       /// 
	unsigned int m_nBinsData;   ///
	unsigned int m_nBr;         /// number of decay branches
	unsigned int m_nGam;        /// max number of gammas per DB
    
    /// gamma energies      
  	double** m_eTruGam;
  	double*  m_eTruAlp;
    /// continuous beta spectra
    double*  m_binCenter;
    double** m_eTru   ;
    double** m_eTruBck;
    double*  m_eVis   ;
    double*  m_eVisBck;
    double*  m_eRec   ;
    double*  m_eRecBck;
    double*  m_eTheo   ;
    double*  m_eData   ;
    double*  m_eDataErr;
    
    /// Gauss lookup table
    static bool               s_gausTableReady;
    static const unsigned int s_nGausTable     = 100000;
    static const double       s_gausTableRes;
    static const double       s_gausTableResR;
    static double             s_gausTable[s_nGausTable];
   
    double m_eMinDraw;
    double m_eMaxDraw;
    double m_eMin;
    double m_eMax;
    double m_lastNormScale;
    double m_fitMin;
    double m_fitMax;
    double m_binWidth;
    bool   m_opt;
    bool   m_dataIsLoaded;
    
    int    m_fitMinBin;
    int    m_fitMaxBin;
    
    string m_name;
    string m_title;
    
            void PrepGaus            ();
            void AddGamma            (string name,
                                      string pdfName,
                                      double eTruGam);
            void InitToyMC           (string fileName);
            void TheoHistTree        (string fileName,
                                      int isotope=0,
                                      int branchOffset=0,
                                      double componentScale=1.0);
            void DataHist            (string fileName);
            void AddBackground       ();
            void Normalize           ();
            void ApplyScintillatorNL ();
            void ApplyElectronicsNL  ();
            void FillComponentRec    (double* eRecOut,
                                      int brFirst,
                                      int brLast);
          double GetEVisGamma        (double eTruGam);
	  double WMCorrection        (string name_WM,int branchIdx_WM,double T_WM);
    virtual void SetParameters       ()                = 0;
    virtual void InitTheo            ()                = 0;
    virtual void InitData            (string fileName) = 0;
    
    TH1F PlotSpec(int type);
   
    static std::vector<dybGammaPeak> s_gammaPeaks;
};

#endif
