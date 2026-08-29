#include "dybBi212Data.h"

unsigned int dybBi212Data::s_nMaxBins     = 12000;
//unsigned int dybBi212Data::s_nMaxBinsData = 80;
unsigned int dybBi212Data::s_nMaxBinsData = 75;
unsigned int dybBi212Data::s_nMaxBr       = 10;
unsigned int dybBi212Data::s_nMaxGam      = 2;

void dybBi212Data::SetParameters()
{
  m_eMinDraw     = 0;
  m_eMin         = 0;
  m_eMax         = 3.0;
  //m_fitMin       = 1.1;
  m_fitMin       = 0.8;
  //m_fitMin       = 0.55;
  m_fitMax       = 2.8;
  m_name         = "Bi212";
  m_title        = "Bi212";
}
void dybBi212Data::InitTheo()
{
  std::cout << " calculating theoretical Bi212 shape " << std::endl;
  TheoHistTree("necessaryfiles/input/theo/bi212_hist.root");
}
void dybBi212Data::InitData(string fileName)
{
  std::cout << " ----> Reading Bi212 data from " << fileName << std::endl;
  string filename = fileName;
  TFile* file = new TFile(filename.c_str());
  TH1F* sigH  = (TH1F*)file->Get("bi212");
  
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
  /*
  for (int i=0;i!=m_nBinsData;i++)
  {
    m_eData   [i] = 0;
    m_eDataErr[i] = 0;
  }
*/
}
