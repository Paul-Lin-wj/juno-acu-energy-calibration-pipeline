#include "dybK40Data.h"
#include "TROOT.h"

unsigned int dybK40Data::s_nMaxBins     = 20000;
unsigned int dybK40Data::s_nMaxBinsData = 80;//200
unsigned int dybK40Data::s_nMaxBr       = 3;
unsigned int dybK40Data::s_nMaxGam      = 1;

void dybK40Data::SetParameters()
{
  std::cout<<"running dybK40Data::SetParameters()"<<std::endl;
  m_eMinDraw     = 0;
  m_eMin         = 0;
  m_eMax         = 2.0;
  m_fitMin       = dybParameters::k40FitMinE;
  m_fitMax       = dybParameters::k40FitMaxE;
  m_name         = "K40";
  m_title        = "K40";
}
void dybK40Data::InitTheo()
{
  std::cout<<"running dybK40Data::InitTheo()"<<std::endl;
  std::cout << " calculating theoretical K40 shape " << std::endl;
  TheoHistTree("necessaryfiles/input/theo/K40_hist.root");
  //TheoHistTree("/lustrefs/juno26/users/zhaorz/Calib/fitter_EnergyNL_DYBmodel/necessaryfiles/input/theo/K40_hist.root");
}
void dybK40Data::InitData(string fileName)
{
  std::cout<<"running dybK40Data::InitData"<<std::endl;
  std::cout << " ----> Reading K40 data from " << fileName << std::endl;
  TFile* file = new TFile(fileName.c_str());
  if (!file || file->IsZombie()) {
    std::cerr << "ERROR: cannot open K40 data file: " << fileName << std::endl;
    exit(1);
  }
  TH1F* sigH = (TH1F*)file->Get("K40");
  if (!sigH) {
    sigH = (TH1F*)file->Get("spec_10m_rebin2");
  }
  if (!sigH) {
    std::cerr << "ERROR: histogram K40 or spec_10m_rebin2 missing in " << fileName << std::endl;
    file->Close();
    delete file;
    exit(1);
  }

  for (int i=0;i!=m_nBinsData;i++)
  {
    double content = sigH->GetBinContent(i+1);
    double error   = sigH->GetBinError  (i+1);
    m_eData   [i] = content;
    m_eDataErr[i] = error;
  }
  delete sigH;
  file->Close();
  delete file;
}
