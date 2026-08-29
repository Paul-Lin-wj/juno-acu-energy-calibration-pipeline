#include "dybB12Data.h"
#include "TROOT.h"

unsigned int dybB12Data::s_nMaxBins     = 14400;
//unsigned int dybB12Data::s_nMaxBins     = 28800;
unsigned int dybB12Data::s_nMaxBinsData = 80;
//unsigned int dybB12Data::s_nMaxBinsData = 72;
unsigned int dybB12Data::s_nMaxBr       = 5;
unsigned int dybB12Data::s_nMaxGam      = 2;

void dybB12Data::SetParameters()
{
	m_eMinDraw     = 0;
	m_eMin         = 0;//0; -0.125
	m_eMax         = 20;//18; 17.875
	m_fitMin       = dybParameters::b12FitMinE;
	m_fitMax       = dybParameters::b12FitMaxE;
	m_name         = "B12";
	m_title        = "B12";
}
void dybB12Data::InitTheo()
{
	//std::cout << " calculating theoretical B12 shape " << std::endl;

	const char* predDir = "necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/";
	//const char* predDir = "necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/";
	TheoHistTree(Form("%s12B_pure_beta_0_20MeV_80bins.root", predDir));
	TheoHistTree(Form("%s12N_pure_beta_0_20MeV_80bins.root", predDir), 1);
	// Generate spectrum at dybSpectrum.cxx
}
void dybB12Data::InitData(string fileName)
{
	std::cout << " ----> Reading B12 data from " << fileName << std::endl;

	TFile* file = new TFile(fileName.c_str());
	TH1D* sigH  = (TH1D*)file->Get("B12_data");     //JUNO P26B
	//TH1F* sigH  = (TH1F*)file->Get("spec");
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
