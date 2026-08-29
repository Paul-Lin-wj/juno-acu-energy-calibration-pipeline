#ifndef dybGammaPeak_h
#define dybGammaPeak_h

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
#include "TMath.h"
#include "TString.h"
#include "TGraph.h"
#include "TGraphErrors.h"
#include "dybEnergyModel.h"
#include "dybParameters.h"
//#include "dybData.h"

using namespace std;

//class dybParameters;

class dybGammaPeak 
{
  public:
    dybGammaPeak();
    dybGammaPeak(string peakName,
                 string pdfName,
                 double eTru_total ,
                 double eTru_single);
   ~dybGammaPeak();
    
    void  Init(string peakName,  string pdfName,
               double eTru_total,double eTru_single);
               
    void   SetEScale     (double gamScale);
    void   SetERec       (double val);
    void   SetERecError  (double val){m_eRecError = val;}    
    void   SetBiasOS     (double val){m_biasOS    = val;}  
    void   UpdateTheoNL  ();          
    void   UpdateDataNL  ();  
                         
    double GetChi2       ();        
    
    static double s_gamScale;
    static double s_reflectivity;
    string GetName       () {return m_name;       }
    double GetERec       () {return m_eRec     ;  }
    double GetEVis       () {return m_eVis     ;  }
    double GetERecError  () {return sqrt(pow(m_eRecError,2)+pow(m_eVisError,2));  }
    double GetETruSingle () {return m_eTru_single;}
    double GetETruTotal  () {return m_eTru_total; }
    double GetDataScintNL() {return m_dataScintNL;}
    double GetDataFullNL () {return m_dataFullNL; }
    double GetTheoScintNL() {return m_theoScintNL;}
    double GetTheoFullNL () {return m_theoFullNL; }
    double GetEffectiveEnergy();
    bool   IsSingleGamma(){if(fabs(m_eTru_single-m_eTru_total)<0.1) return true; else return false;}
  private:
    static int s_count;
    string m_name;
    double m_eTru_single; 
    double m_eTru_total; 
    double m_eVis; 
    double m_eVisError; 
    double m_eRec; 
    double m_eRecError; 
    double m_eRecRaw; 
    double m_error; 
    double m_biasOS; 
    double m_theoScintNL;
    double m_dataScintNL;
    double m_theoFullNL;
    double m_dataFullNL;
    bool   m_includeInFit;
    
    /// PDF of primary e+/e- to fold with electron NL
    static const unsigned int m_nMaxPdf = 10000;  
                 unsigned int m_nPdf;  
                 unsigned int m_nPdf_anchor;  
    double        m_pdf_eTru [m_nMaxPdf];
    double        m_pdf_prob [m_nMaxPdf];
    double        m_pdf_prob2[m_nMaxPdf];
    double        m_pdf_prob3[m_nMaxPdf];
    double        m_pdf_prob4[m_nMaxPdf];
    double        m_pdf_eTru_anchor[m_nMaxPdf];
    double        m_pdf_prob_anchor[m_nMaxPdf];

    double m_eRec_anchor; 
    double m_eTru_total_anchor; 
    double m_eVis_anchor; 
    double m_dataFullNL_anchor;
    double m_theoScintNL_anchor;
    double m_theoFullNL_anchor;
};
  
#endif
