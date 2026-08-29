#ifndef dybParameters_h
#define dybParameters_h

#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

enum ScintillatorParametrization {
  kSimpleEmpirical,
  kLowECorrEmpirical,
  kPhysics
};
enum ElectronicsParametrization {
  kSingleExponential,
  kDoubleExponential,
  kPolynomial
};

class dybParameters
{
  public:
    
    static int nFitParameter;
    static double p0_start;
    static double p1_start;
    static double p2_start;
    static double p3_start;
    static double alpha_start;
    static double alphaError;
    static double tau_start;
    static double tauError;
    static double alpha2_start;
    static double tau2_start;
    static double gamScale_start;
    static double kB_alpha_start;
    static double lsScale_start;
    static double k40Scale_start;
    
    static int fitPrintLevel;
    static std::string quenching_file;
    static std::string fadcData_file;
    
    static std::string lsData_file_LBNL;
    static std::string lsData_file_IHEP;
    
    static std::string gammaData_file;
    static std::string gammaPdf_file;
    static std::string b12Data_file;
    static std::string c11Data_file;
    static std::string c10Data_file;
    static std::string k40Data_file;
    static std::string bi212Data_file;
    static std::string bi214Data_file;
    static std::string tl208Data_file;
    static std::string michelData_file;
    static std::string alphaData_file;
    
    static bool fitNGd;
    static bool fitGamma;
    static bool fitIbd;
    static bool fitB12;
    static bool fitC11;
    static bool fitC10;
    static bool fitK40;
    static bool fitBi212;
    static bool fitBi214;
    static bool fitTl208;
    static bool fitLsLBNL;
    static bool fitLsIHEP;
    static bool fitFadc;
    static bool fitMichel;
    static bool fitAlpha;
    
    static bool fixScintP0;
    static bool fixScintP1;
    static bool fixScintP2;
    static bool fixScintP3;
    static bool fixKBAlpha;
    static bool fixElecP0;
    static bool fixElecP1;
    static bool fixElecP2;
    static bool fixElecP3;
    static bool fixN12;
    static bool fixGamScale;
    static bool fixReflectivity;
    static bool fixLsScale;
    static bool fixFadcNor;
    static bool fixFadcRes;
    static bool fixK40Scale;
    static bool constrainTau;
    static bool constrainFadc;    
    static bool constrainWM;

    static int b12_nEventsTheo;
    static int b12_nBinsTheo;
    static int b12_nBinsData;

    static int c11_nEventsTheo;
    static int c11_nBinsTheo;
    static int c11_nBinsData;

    static int c10_nEventsTheo;
    static int c10_nBinsTheo;
    static int c10_nBinsData;

    static int k40_nEventsTheo;
    static int k40_nBinsTheo;
    static int k40_nBinsData;    

    static double anchorEnergy;
    
    static double b12FitMinE;
    static double b12FitMaxE;
    static double c11FitMinE;
    static double c11FitMaxE;
    static double c10FitMinE;
    static double c10FitMaxE;
    static double c10C11Frac_start;
    static double c10Be11Frac_start;
    static double b12VertexCut;
    static double n12Ratio;
    static double n12RatioError;
    static double fadcNor;
    static double fadcNorError;
    static double fadcRes;
    static double fadcResError;

    static double k40FitMinE;
    static double k40FitMaxE;
    static double k40Scale;
    static double k40ScaleError;

    static double b12Branch0;
    static double b12Branch0Error;
    static double b12Branch1;
    static double b12Branch1Error;
    static double b12Branch2;
    static double b12Branch2Error;
    static double n12Branch0;
    static double n12Branch0Error;
    static double n12Branch1;
    static double n12Branch1Error;
    static double n12Branch2;
    static double n12Branch2Error;
    static double n12Branch3;
    static double n12Branch3Error;
    static double n12Branch4;
    static double n12Branch4Error;

    static double universalWM;
    static double WMError;

    static double elecTauMax;
    static double elecTauSigma;
    static double ibdWeight;
    static double b12Weight;
    static double c11Weight;
    static double c10Weight;
    static double k40Weight;
    static double FadcWeight;
    static double bi212Weight;
    static double bi214Weight;
    static double tl208Weight;
    static double lsLBNLWeight;
    
    static double gamScale;
    static double gamScaleError;
    static double nominalReflectivity;
    static double reflectivityError;
    
    static ScintillatorParametrization scintillatorParametrization;
    static ElectronicsParametrization  electronicsParametrization;
    
    static std::string plotFormat;
    static std::string plotFolder;
    
    static bool doFullAnalysis;
    static std::string toyKey;
    static std::string title;
    static std::string toyFolder;
    static int         nToy;
};

#endif
