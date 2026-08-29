#include "dybParameters.h"

typedef dybParameters DYBP;
typedef ScintillatorParametrization SP;
typedef ElectronicsParametrization EP;

SP DYBP::scintillatorParametrization = kPhysics;
//SP DYBP::scintillatorParametrization = kSimpleEmpirical;
//SP DYBP::scintillatorParametrization = kLowECorrEmpirical;
EP DYBP::electronicsParametrization  = kSingleExponential;
//EP DYBP::electronicsParametrization  = kDoubleExponential;
//EP DYBP::electronicsParametrization  = kPolynomial;

int DYBP::nFitParameter     = 13;
int DYBP::fitPrintLevel     = 1;
bool DYBP::doFullAnalysis   = true;

/// IHEP nominal lowE corr

/// March 2015 nominal
//double DYBP::p0_start       = 1.04689;//Only for noGamma fit and Fix it
double DYBP::p0_start       = 1.0;
//double DYBP::p0_start       = 1.0149868;//fixed. for JUNO OMILREC energy anchored at nH
double DYBP::p1_start       = 10.0;
double DYBP::p2_start       = 4;
double DYBP::p3_start       = 0.;
//double DYBP::alpha_start    = 0.103615;
double DYBP::alpha_start    = 0.1;
double DYBP::alphaError     = 4.374e-03;
//double DYBP::tau_start      = 2.20351;
double DYBP::tau_start      = 40;
double DYBP::tauError       = 0.10394;
double DYBP::alpha2_start   = 0.08;
double DYBP::tau2_start     = 2.2 ;
double DYBP::gamScale_start = 1.0;
//double DYBP::gamScale_start = 1.0;
double DYBP::k40Scale_start  = 1.0;
double DYBP::lsScale_start  = 1.0;

/// Spectra fit
double DYBP::kB_alpha_start = 7.7;

double DYBP::gamScale       = 1.0;
//double DYBP::gamScale       = 0.99937;
double DYBP::gamScaleError  = 0.005;
//double DYBP::gamScaleError  = 0.0015;
//double DYBP::gamScaleError  = 0.015;
//double DYBP::nominalReflectivity  = 0.01;
double DYBP::nominalReflectivity  = 0.1;
double DYBP::reflectivityError  = 0.5;
double DYBP::n12Ratio       = 0.02575;
double DYBP::n12RatioError  = 0.01;
double DYBP::fadcNor  = 1.0;
double DYBP::fadcNorError   = 0.002;
double DYBP::fadcRes  = 0.; 
double DYBP::fadcResError   = 0.005;
double DYBP::k40Scale = 1.0;
double DYBP::k40ScaleError  = 0.005;

// Normalized BR from predSpec_fromChengzhuo_IHEP (fixed in fit)
double DYBP::b12Branch0     = 0.982780;
double DYBP::b12Branch0Error   = 0.0;
double DYBP::b12Branch1     = 0.011820;
double DYBP::b12Branch1Error   = 0.0;
double DYBP::b12Branch2     = 0.005400;
double DYBP::b12Branch2Error   = 0.0;
double DYBP::n12Branch0     = 0.962835;
double DYBP::n12Branch0Error   = 0.0;
double DYBP::n12Branch1     = 0.019003;
double DYBP::n12Branch1Error   = 0.0;
double DYBP::n12Branch2     = 0.014117;
double DYBP::n12Branch2Error   = 0.0;
double DYBP::n12Branch3     = 0.004045;
double DYBP::n12Branch3Error   = 0.0;
double DYBP::n12Branch4     = 0.0;
double DYBP::n12Branch4Error   = 0.0;
double DYBP::universalWM     = 0.0048;
double DYBP::WMError    = 0.002;

bool DYBP::fitGamma  = true;    //true
bool DYBP::fitNGd    = false;
bool DYBP::fitB12    = true;   //true
bool DYBP::fitC11    = true;   //true
bool DYBP::fitC10    = true;   //true
bool DYBP::fitK40    = false;
bool DYBP::fitBi212  = false;
bool DYBP::fitBi214  = false;
bool DYBP::fitTl208  = false;
bool DYBP::fitLsLBNL = false;
bool DYBP::fitLsIHEP = false;
bool DYBP::fitFadc   = false;    //true
bool DYBP::fitMichel = false;
bool DYBP::fitAlpha  = false;
bool DYBP::constrainTau = false;
bool DYBP::constrainFadc = false;
bool DYBP::constrainWM = false;

bool DYBP::fitIbd    = false;

bool DYBP::fixScintP0   = false; //energy scale
bool DYBP::fixScintP1   = false; //kb
bool DYBP::fixScintP2   = false; //Cherenkov
bool DYBP::fixScintP3   = true; // radiation
bool DYBP::fixKBAlpha   = true;
bool DYBP::fixElecP0    = false;    //false
bool DYBP::fixElecP1    = false;    //false
bool DYBP::fixElecP2    = true;
bool DYBP::fixElecP3    = true;
bool DYBP::fixN12       = false;
bool DYBP::fixGamScale  = false;     // fix nH energy scale
bool DYBP::fixReflectivity  = true;
bool DYBP::fixLsScale   = true;
bool DYBP::fixFadcNor   = false;
bool DYBP::fixFadcRes   = false;
bool DYBP::fixK40Scale   = true;

//string DYBP::toyKey          = "nom_AdScaled";
//string DYBP::toyKey          = "nom_AdSimpleNL";
//string DYBP::toyKey          = "shape";
//string DYBP::title           = "Fit to #gamma only";
//string DYBP::title           = "MC shape fit";
string DYBP::title           = "Default fit";
int    DYBP::nToy            = 10;

//double DYBP::anchorEnergy    = 2.4919;
//double DYBP::anchorEnergy    = 8.05;//scale elec NL from Co to nGd
double DYBP::anchorEnergy    = 2.223;

double DYBP::elecTauMax      = 3.0;
double DYBP::elecTauSigma    = 0.25;

double DYBP::ibdWeight       = 1.0;
double DYBP::b12Weight       = 1.0;
double DYBP::c11Weight       = 1.0;
double DYBP::c10Weight       = 1.0;
double DYBP::k40Weight       = 10./80.;
double DYBP::FadcWeight      = 1.;
double DYBP::lsLBNLWeight    = 1.;
double DYBP::bi212Weight     = 0.1;
double DYBP::bi214Weight     = 0.5;
double DYBP::tl208Weight     = 0.5;

//double DYBP::b12FitMinE      = 3.5;
//double DYBP::b12FitMaxE      = 18.;
double DYBP::b12FitMinE      = 3.5;
double DYBP::b12FitMaxE      = 17;  //16
double DYBP::b12VertexCut    = 0.80;

double DYBP::c11FitMinE      = 0.9; //0.9
double DYBP::c11FitMaxE      = 2.0; //1.9
double DYBP::c10FitMinE      = 1.0;
double DYBP::c10FitMaxE      = 4.0; //3.5
double DYBP::c10C11Frac_start  = 0.15;
double DYBP::c10Be11Frac_start = 0.02;

double DYBP::k40FitMinE      = 0.8;
double DYBP::k40FitMaxE      = 1.6;

int   DYBP::b12_nEventsTheo = 20000000;
int   DYBP::b12_nBinsTheo   = 28800;
int   DYBP::b12_nBinsData   = 80;

int   DYBP::c11_nEventsTheo = 20000000;
int   DYBP::c11_nBinsTheo   = 28800;
int   DYBP::c11_nBinsData   = 200;
//int   DYBP::c11_nBinsData   = 80;
 
int   DYBP::c10_nEventsTheo = 20000000;
int   DYBP::c10_nBinsTheo   = 28800;
int   DYBP::c10_nBinsData   = 80;
 
int   DYBP::k40_nEventsTheo = 20000000;
int   DYBP::k40_nBinsTheo   = 28800;
int   DYBP::k40_nBinsData   = 80;//200

//string DYBP::toyKey          = "nom_JUNO_OMILREC";
//string DYBP::toyKey          = "nom_JUNO_OMILREC_B12_nofadc_rawGammaUnc";
//string DYBP::toyKey          = "nom_JUNO_OMILREC_B12v2_elecNL_005GammaUnc_r15";
string DYBP::plotFormat       = "pdf";
string DYBP::toyFolder        = "files/input/toy/";
//string DYBP::plotFolder       = "plots/JUNO_dybB12pred/";
//string DYBP::plotFolder       = "plots/JUNO/noB12/";
//string DYBP::plotFolder       = "plots/JUNO/B12v2_ElecNL/";
//string DYBP::plotFolder       = "plots/JUNO/B12_nofadc/";
//string DYBP::plotFolder       = "plots/JUNO/B12_nofadc_01GammaUnc/";
//string DYBP::plotFolder       = "plots/JUNO/";
string DYBP::plotFolder       = "plots/JUNO/26B/";

string DYBP::quenching_file   = "necessaryfiles/input/Quenching.root";
//string DYBP::gammaData_file   = "necessaryfiles/input/JUNO/P25B/Ge68_0823_Ge68Map_v11.3_JUNO_005.dat";
//string DYBP::gammaData_file   = "necessaryfiles/input/JUNO/P25C/gamma_P25C.dat";
//string DYBP::gammaData_file   = "necessaryfiles/input/JUNO/ReProd26B/gamma_Phase1_K40.dat";
string DYBP::gammaData_file   = "necessaryfiles/input/JUNO/ReProd26B/gamma_AllPhase.dat";

//string DYBP::toyKey          = "nom_JUNO_26B_noGamma_finalCorrection_AllPhase_FVcutR0_1720";
string DYBP::toyKey          = "nom_JUNO_26B_finalCorrection_AllPhase_FVcutR0_1720";

//string DYBP::b12Data_file     = "necessaryfiles/input/JUNO/P25B/omilrec_B12_v2.root";
string DYBP::b12Data_file     = "necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root";
string DYBP::c11Data_file     = "necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root";
string DYBP::c10Data_file     = "necessaryfiles/input/JUNO/ReProd26B/Spec/forNLfitter/Isotope_data_AllPhase_FVcutR0_1720_Finalcorrection.root";

string DYBP::k40Data_file     = "necessaryfiles/input/K40.root";
string DYBP::bi212Data_file   = "necessaryfiles/input/bi212.root";
string DYBP::bi214Data_file   = "necessaryfiles/input/bi214.root";
string DYBP::tl208Data_file   = "necessaryfiles/input/tl208.root";

string DYBP::fadcData_file    = "necessaryfiles/input/FADC_scaleNL.txt";
string DYBP::lsData_file_LBNL = "necessaryfiles/input/LS_LBNL_2015_short.dat";
string DYBP::lsData_file_IHEP = "necessaryfiles/input/LS_IHEP.dat";
string DYBP::alphaData_file   = "files/input/alpha/alphaPeaks_P14A_AdScaled.dat";


string DYBP::gammaPdf_file    = "necessaryfiles/input/Gamma_Electron.root";
string DYBP::michelData_file  = "files/input/spectra/data/michel_fidVol_jul2015.root";
