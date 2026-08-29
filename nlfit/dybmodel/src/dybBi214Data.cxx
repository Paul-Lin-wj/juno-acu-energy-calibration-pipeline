#include "dybBi214Data.h"

unsigned int dybBi214Data::s_nMaxBins     = 5000;
unsigned int dybBi214Data::s_nMaxBinsData = 100;
unsigned int dybBi214Data::s_nMaxBr       = 183;
unsigned int dybBi214Data::s_nMaxGam      = 3;

void dybBi214Data::SetParameters()
{
  std::cout << " setting Bi214 Par " << std::endl;
  m_eMinDraw     = 1.0;
  m_eMin         = 0;
  m_eMax         = 4.0;
  m_fitMin       = 1.32;
  m_fitMax       = 3.8;
  m_name         = "Bi214";
  m_title        = "Bi214";
}
void dybBi214Data::InitTheo()
{
  std::cout << " calculating theoretical Bi214 shape " << std::endl;
  TheoHistTree("necessaryfiles/input/theo/bi214_hist.root");
}
void dybBi214Data::InitData(string fileName)
{
  std::cout << " ----> Reading Bi214 data from " << fileName << std::endl;
  TFile* file = new TFile(fileName.c_str());
  TH1F* sigH  = (TH1F*)file->Get("bi214");

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
