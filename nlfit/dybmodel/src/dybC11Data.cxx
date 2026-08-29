#include "dybC11Data.h"
#include "TROOT.h"

unsigned int dybC11Data::s_nMaxBins     = 14400;
//unsigned int dybC11Data::s_nMaxBins     = 28800;
unsigned int dybC11Data::s_nMaxBinsData = 200;
//unsigned int dybC11Data::s_nMaxBinsData = 80;
//unsigned int dybC11Data::s_nMaxBinsData = 72;
unsigned int dybC11Data::s_nMaxBr       = 1;
unsigned int dybC11Data::s_nMaxGam      = 1;

void dybC11Data::SetParameters()
{
	m_eMinDraw     = 0.5;
	m_eMaxDraw     = 2.5;
	m_eMin         = 0;//0; -0.125
	m_eMax         = 4;//18; 17.875
	m_fitMin       = dybParameters::c11FitMinE;
	m_fitMax       = dybParameters::c11FitMaxE;
	m_name         = "C11";
	m_title        = "C11";
}
void dybC11Data::InitTheo()
{
	//std::cout << " calculating theoretical C11 shape " << std::endl;

	TheoHistTree("necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/11C_pure_beta_0_4MeV_200bins.root");
	//TheoHistTree("necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/11C_pure_beta_0_4MeV_200bins.root");
	// Generate spectrum at dybSpectrum.cxx
}
void dybC11Data::InitData(string fileName)
{
	std::cout << " ----> Reading C11 data from " << fileName << std::endl;

    //gROOT->cd();
	//TFile* file = TFile::Open(fileName.c_str(), "READ");
	TFile* file = new TFile(fileName.c_str());
	TH1D* sigH  = (TH1D*)file->Get("C11_data");     //JUNO C11
	for (int i=0;i!=m_nBinsData;i++)
	{
		double content = sigH->GetBinContent(i+1);
		double error   = sigH->GetBinError  (i+1);
		m_eData   [i] = content;
		m_eDataErr[i] = error;
		cout<<content<<' '<<error<<endl;
	}
	//delete sigH;
	file->Close();
	//delete file;
}
