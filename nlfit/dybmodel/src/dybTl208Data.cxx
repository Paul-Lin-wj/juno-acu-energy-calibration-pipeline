#include "dybTl208Data.h"

unsigned int dybTl208Data::s_nMaxBins     = 1800;
//unsigned int dybTl208Data::s_nMaxBinsData = 180;
unsigned int dybTl208Data::s_nMaxBinsData = 150;
unsigned int dybTl208Data::s_nMaxBr       = 13;
unsigned int dybTl208Data::s_nMaxGam      = 4;

void dybTl208Data::SetParameters()
{
  /// input data histogram: 1200 bins for 0-12 MeV
  m_eMinDraw = 3.0;
  m_eMin     = 0;
  //m_eMax     = 5.4;
  m_eMax     = 6.0;
  //m_fitMin   = 3.53;
  //m_fitMin   = 3.2;
  m_fitMin   = 3.0;
  //m_fitMax   = 4.6;
  m_fitMax   = 5.5 ;
  m_name     = "Tl208";
  m_title    = "Tl208";
}
void dybTl208Data::InitTheo()
{
  std::cout << " calculating theoretical Tl208 shape " << std::endl;
  TheoHistTree("necessaryfiles/input/theo/tl208_hist.root");
}
void dybTl208Data::InitData(string fileName)
{
  std::cout << " ----> Reading Tl208 data from " << fileName << std::endl;
  TFile* file = new TFile(fileName.c_str());
  TH1F* sigH  = (TH1F*)file->Get("tl208");
  
  //TFile* file = new TFile("files/input/spectra/data/Tl208_save.root");
  //TH1F* sigH  = (TH1F*)file->Get("Data_1");
  //sigH->Rebin(3);
  
  //int offset = int(m_eMin/sigH->GetBinWidth(1));
  int offset = 0;
  for (int i=0;i!=m_nBinsData;i++)
  {
    double content = sigH->GetBinContent(offset+i+1);
    double err     = sigH->GetBinError  (offset+i+1);
    m_eData   [i]  = content;
    m_eDataErr[i]  = err;
  }
  delete sigH;
  file->Close();
  delete file;
}
