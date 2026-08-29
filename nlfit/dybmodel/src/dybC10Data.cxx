#include "dybC10Data.h"
#include "TROOT.h"

unsigned int dybC10Data::s_nMaxBins     = 14400;
//unsigned int dybC10Data::s_nMaxBins     = 28800;
unsigned int dybC10Data::s_nMaxBinsData = 80;
//unsigned int dybC10Data::s_nMaxBinsData = 72;
unsigned int dybC10Data::s_nMaxBr       = 7;
unsigned int dybC10Data::s_nMaxGam      = 2;

void dybC10Data::SetParameters()
{
	m_eMinDraw     = 0;
	m_eMin         = 0;//0; -0.125
	m_eMax         = 4;//18; 17.875
	m_fitMin       = dybParameters::c10FitMinE;
	m_fitMax       = dybParameters::c10FitMaxE;
	m_name         = "C10";
	m_title        = "C10";
}
void dybC10Data::InitTheo()
{
	//std::cout << " calculating theoretical C10 shape " << std::endl;

	const char* predDir = "necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/forNLfitter/";
	//const char* predDir = "necessaryfiles/input/JUNO/ReProd26B/predSpec_fromChengzhuo_IHEP/";
	TheoHistTree(Form("%s10C_pure_beta_0_4MeV_80bins.root", predDir), 0, 0, 1.0);
	TheoHistTree(Form("%s11C_pure_beta_0_4MeV_80bins.root", predDir), 0, 2, s_c10C11Frac);
	TheoHistTree(Form("%s11Be_pure_beta_0_4MeV_80bins.root", predDir), 0, 3, s_c10Be11Frac);
	// Generate spectrum at dybSpectrum.cxx
}
void dybC10Data::InitData(string fileName)
{
	std::cout << " ----> Reading C10 data from " << fileName << std::endl;

    //gROOT->cd();
	//TFile* file = TFile::Open(fileName.c_str(), "READ");
	TFile* file = new TFile(fileName.c_str());
    if(!file){
        cout<<"C10 File is null?"<<endl;
    }
    else
        cout<<"File reading."<<endl;
	TH1D* sigH  = (TH1D*)file->Get("C10_data_pair");     //JUNO C11
    
	for (int i=0;i!=m_nBinsData;i++)
	{
		double content = sigH->GetBinContent(i+1);
		double error   = sigH->GetBinError  (i+1);
		m_eData   [i] = content;
		m_eDataErr[i] = error;
		cout<<content<<' '<<error<<endl;
	}
	//delete sigH;
	//file->Close();
	//delete file;
}
