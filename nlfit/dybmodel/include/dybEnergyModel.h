#ifndef dybEnergyModel_h
#define dybEnergyModel_h

#include <vector>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <math.h>
#include "TFile.h"
#include "TChain.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TMath.h"
#include "TF1.h"
#include "TStyle.h"
#include "TString.h"
#include "TGraph.h"
#include "TGraphErrors.h"
#include "TGraphAsymmErrors.h"

#include "dybParameters.h"
#include "dybGammaPeak.h"
//#include "dybSpectrum.h"

using namespace std;

class dybEnergyModel{
	public:
		dybEnergyModel();

		static double GetKB      () {return s_kB;}
		static double GetKBAlpha () {return s_kB_alpha;}
		
		static void SetScintP0 (double val){s_p0=val;}
		static void SetScintP1 (double val){ s_p1=val;s_kB =val;
			if(val>24.9){s_p1=s_kBMax;s_kB =s_kBMax;}
			//if(val<2.1) {s_p1=s_kBMin;s_kB =s_kBMin;}
                        if(val<4.0) {s_p1=s_kBMin;s_kB =s_kBMin;}
			Update();
		}
		static void SetKBAlpha (double val){ s_kB_alpha =val;
                        if(val>24.9){s_kB_alpha =s_kBMax_alpha;}
                        //if(val<2.1) {s_kB_alpha =s_kBMin_alpha;}
			if(val<4.0) {s_kB_alpha =s_kBMin_alpha;}
			Update();
		}
		static void SetScintP2 (double val){s_p2=val;s_cer=val;}
		static void SetScintP3 (double val){s_p3=val;s_rad=val;
			if(val>1)s_rad=val=1;
			if(val<0)s_rad=val=0;
		}
		static void SetElecP0  (double val){s_alp1=val;
			//if(val<0)s_alp1=0;
		}
		static void SetElecP1  (double val){s_tau1=val;
			//if(val<0.01)s_tau1=0.01;
		}
		static void SetElecP2  (double val){s_alp2=val;
			if(val<0)s_alp2=0;
		}
		static void SetElecP3  (double val){s_tau2=val;
			if(val<0.01)s_tau2=0.01;
		}
		
		static void SetPull0   (double val){s_b12EPull =val;}
		
		static std::string s_key;
			
		static void   Load  ();
		static void   Update();
		static double ScintillatorNL(double eTrue);
		static double AlphaNL       (double eTrue);
		static double ElectronicsNL (double eVis);
		static double Resolution    (double eVis);
                static double Resolution_K40    (double eVis);//20171016
		
		static void SaveCurves();
		
		static TGraph DrawElectronScintNL(int nSamples = 10000,double eMax=12);
		static TGraph DrawGammaScintNL   (int nSamples = 10000,double eMax=12);
		static TGraph DrawPositronScintNL(int nSamples = 10000,double eMax=12);
		static TGraph DrawAlphaScintNL   (int nSamples = 10000,double eMax=12);
		static TGraph DrawElectronFullNL (int nSamples = 10000,double eMax=12);
		static TGraph DrawGammaFullNL    (int nSamples = 10000,double eMax=10);
		static TGraph DrawPositronFullNL (int nSamples = 10000,double eMax=10);
		static TGraph DrawAlphaFullNL    (int nSamples = 10000,double eMax=10);
		
		static vector<double> SampleElectronicsNL  (int nSamples,double eMax=12);
		static vector<double> SampleElectronScintNL(int nSamples,double eMax=12);
		static vector<double> SampleElectronFullNL (int nSamples,double eMax=12);
		static vector<double> SamplePositronScintNL(int nSamples,double eMax=12);
		static vector<double> SamplePositronFullNL (int nSamples,double eMax=12);
		static vector<double> SampleAlphaScintNL   (int nSamples,double eMax=12);
		static vector<double> SampleAlphaFullNL    (int nSamples,double eMax=12);
		
		static TGraph DrawElectronicsNL(int nSamples = 1000,double eMax=12);
		
		static double  s_p0;
		static double  s_p1;
		static double  s_p2;
		static double  s_p3;
	 
		static double  s_cer;
		static double  s_rad;
		
		static double  s_alp1;
		static double  s_alp2;
		static double  s_tau1;
		static double  s_tau2;
                //static double  s_fadcScale;
		
		static double  s_gamScale;
		static double  s_b12EPull;
		static bool    s_lowECorr;
		static double  s_gammaCutoff;
		
	private: 
		static double  s_kB;
		static double  s_kB_alpha;
		static bool    s_isLoaded;
		static int     s_kBIdx;
		static double  s_kBResid;
		static double  s_kBResid_alpha;
		static double  s_normEnergy;
		static const double s_kBMax;
		//static const double s_kBMin = 2.1;
		static const double s_kBMax_alpha;
		//static const double s_kBMin_alpha = 2.1;
                static const double s_kBMin;
                static const double s_kBMin_alpha;
		
		/// preloaded shapes for Birks-based scintillator model
		//static const unsigned int s_nSamples = 20000;
		//static const unsigned int s_nSamples = 61000;
		static const unsigned int s_nSamples = 20000;
		//static const unsigned int s_nKb      = 256;
                static const unsigned int s_nKb      = 250;
		//static const unsigned int s_nKb      = 22;
		static const double s_samplingRange;
		static const double s_samplingResol;
		
		static double s_energySamples          [s_nSamples];
		static double s_cerenkovShape          [s_nSamples];
		static double s_quenchingShape1 [s_nKb][s_nSamples];
		static double s_quenchingShape2 [s_nKb][s_nSamples];
		static double s_quenchingShapeA[s_nKb][s_nSamples];
		
		static double* s_quenchingShape1_lowKb;
		static double* s_quenchingShape1_higKb;
		static double* s_quenchingShape2_lowKb;
		static double* s_quenchingShape2_higKb;
		static double* s_quenchingShapeA_lowKb;
		static double* s_quenchingShapeA_higKb;
		
		/// NL parameterizations
		static double PhysicsScintillator    (double eTru);
		static double SimpleEmpScintillator  (double eTru);
		static double LowECorrEmpScintillator(double eTru);
		static double SingleExpElectronics   (double eVis);
		static double DoubleExpElectronics   (double eVis);
		static double PolynomialElectronics  (double eVis);
		
		static double ScintillatorShape      (double eTru);
		static double AlphaShape             (double eTru);
		
		static vector<double> m_energySamples;
		static vector<double> m_grummel;
};

#endif
