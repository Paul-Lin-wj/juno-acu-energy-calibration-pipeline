#include "dybMichelData.h"

unsigned int dybMichelData::s_nMaxBins     = 5250;
unsigned int dybMichelData::s_nMaxBinsData = 175;
unsigned int dybMichelData::s_nMaxBr       = 1;
unsigned int dybMichelData::s_nMaxGam      = 0;

void dybMichelData::SetParameters()
{
	std::cout << " setting Michel Parameters " << std::endl;
	m_eMinDraw     = 0;
	m_eMin         = 0;
	m_eMax         = 70.0;
	m_fitMin       = 48.0;
	//m_fitMin       = 42.0;
	//m_fitMin       = 20.0;
	m_fitMax       = 58.0;
	m_name         = "Michel";
	m_title        = "Muon";
}
void dybMichelData::InitTheo()
{
	std::cout << " calculating theoretical Michel spectrum shape " << std::endl;
	TheoHistTree("files/input/spectra/theo/Michel_hist.root");
}
void dybMichelData::InitData(string fileName)
{
	std::cout << " ----> Reading Michel data from " << fileName << std::endl;
	TFile* file = new TFile(fileName.c_str());
	TH1F* sigH  = (TH1F*)file->Get("spectrum");
	int nBinsInput = sigH->GetNbinsX();
	for (int i=0;i!=m_nBinsData;i++)
	{
		if(i>nBinsInput-1) break;
		double content = sigH->GetBinContent(i+1);
		double error   = sigH->GetBinError  (i+1);
		m_eData   [i] = content;
		m_eDataErr[i] = error;
	}
	//delete sigH;
	file->Close();
	delete file;
}
