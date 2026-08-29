#ifndef dybAlphaPeak_h
#define dybAlphaPeak_h

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

class dybAlphaPeak 
{
  public:
    dybAlphaPeak();
    dybAlphaPeak(string peakName,double eTru);
   ~dybAlphaPeak();
    
    void  Init(string peakName,double eTru);
               
    void   SetERec       (double val);
    void   SetERecError  (double val){m_eRecError = val;}    
    void   UpdateTheoNL  ();          
    void   UpdateDataNL  ();  
                         
    double GetChi2       ();        
    
    string GetName       () {return m_name;}
    double GetERec       () {return m_eRec;}
    double GetEVis       () {return m_eVis;}
    double GetERecError  () {return m_eRecError;}
    double GetETru       () {return m_eTru;}
    double GetDataScintNL() {return m_dataScintNL;}
    double GetDataFullNL () {return m_dataFullNL; }
    double GetTheoScintNL() {return m_theoScintNL;}
    double GetTheoFullNL () {return m_theoFullNL; }
  
  private:
    static int s_count;
    string m_name;
    double m_eTru; 
    double m_eVis; 
    double m_eVisError; 
    double m_eRec; 
    double m_eRecError; 
    double m_error; 
    double m_theoScintNL;
    double m_dataScintNL;
    double m_theoFullNL;
    double m_dataFullNL;
    bool   m_includeInFit;
};
  
#endif
