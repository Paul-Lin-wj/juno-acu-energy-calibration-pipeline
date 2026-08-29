#include "dybGlobalFit.h"

dybGammaData *dybGlobalFit::m_gammaData  = 0;
dybB12Data   *dybGlobalFit::m_b12Data    = 0;
dybC11Data   *dybGlobalFit::m_c11Data    = 0;
dybC10Data   *dybGlobalFit::m_c10Data    = 0;
dybK40Data   *dybGlobalFit::m_k40Data    = 0;
dybBi212Data *dybGlobalFit::m_bi212Data  = 0;
dybBi214Data *dybGlobalFit::m_bi214Data  = 0;
dybTl208Data *dybGlobalFit::m_tl208Data  = 0;
dybLSData    *dybGlobalFit::m_lsDataLBNL = 0;
dybLSData    *dybGlobalFit::m_lsDataIHEP = 0;
dybFadcData  *dybGlobalFit::m_fadcData   = 0;
dybMichel*dybGlobalFit::m_michelData = 0;
dybAlphaData *dybGlobalFit::m_alphaData  = 0;

TRandom3 dybGlobalFit::m_rand;
TMinuit* dybGlobalFit::m_minuit = 0;
int    dybGlobalFit::m_nParameter = 13;
int    dybGlobalFit::m_nFreeParameter = 5;
int    dybGlobalFit::m_nFitParameter = 13;
double dybGlobalFit::m_parameters[13];
int    dybGlobalFit::m_printLevel    = 0;
int    dybGlobalFit::m_contourNItr   = 0;
																 
double dybGlobalFit::m_chi2       = 0;
double dybGlobalFit::m_chi2B12    = 0;
double dybGlobalFit::m_chi2C11    = 0;
double dybGlobalFit::m_chi2C10    = 0;
double dybGlobalFit::m_chi2K40    = 0;
double dybGlobalFit::m_chi2Bi212  = 0;
double dybGlobalFit::m_chi2Bi214  = 0;
double dybGlobalFit::m_chi2Tl208  = 0;
double dybGlobalFit::m_chi2Gamma  = 0;
double dybGlobalFit::m_chi2LsLBNL = 0;
double dybGlobalFit::m_chi2LsIHEP = 0;
double dybGlobalFit::m_chi2Fadc   = 0;
double dybGlobalFit::m_chi2Michel = 0;
double dybGlobalFit::m_chi2Alpha  = 0;
double dybGlobalFit::m_chi2Min    = -1;
double dybGlobalFit::m_chi2MinRed = -1;
double dybGlobalFit::m_bestFit     [13];
double dybGlobalFit::m_bestFitError[13];
double dybGlobalFit::m_covMatrix   [13][13];

dybGlobalFit::dybGlobalFit(){
	m_gammaData  = new dybGammaData();
	cout<<"done1"<<endl;
	//michelData = new dybMichel   ();
	m_b12Data    = new dybB12Data  ();
        cout<<"done2"<<endl;
        std::cout<<"running m_k40Data    = new dybK40Data  ()"<<std::endl;
        m_k40Data    = new dybK40Data  ();
	m_bi212Data  = new dybBi212Data();
        cout<<"done3"<<endl;
	m_bi214Data  = new dybBi214Data();
        cout<<"done4"<<endl;
	m_tl208Data  = new dybTl208Data();
        cout<<"done5"<<endl;
	m_lsDataLBNL = new dybLSData   ("LBNL");
        cout<<"done6"<<endl;
	m_lsDataIHEP = new dybLSData   ("IHEP");
        cout<<"done7"<<endl;
	m_fadcData   = new dybFadcData ();
        cout<<"done8"<<endl;
	m_c11Data    = new dybC11Data  ();
        cout<<"done9"<<endl;
	m_c10Data    = new dybC10Data  ();
        cout<<"done10"<<endl;
	//m_alphaData  = new dybAlphaData ();
}
dybGlobalFit::~dybGlobalFit(){
	delete m_gammaData ;
	//delete m_michelData;
	delete m_b12Data   ;
	delete m_c11Data   ;
	delete m_c10Data   ;
        delete m_k40Data;
	delete m_bi212Data ;
	delete m_bi214Data ;
	delete m_tl208Data ;
	//delete m_gammaData ;
	delete m_lsDataLBNL;
	delete m_lsDataIHEP;
	delete m_fadcData  ;
	//delete m_alphaData ;
}
void dybGlobalFit::LoadData(){
	std::cout << " ---> Start loading data " << std::endl;
	if (dybParameters::fitGamma) {
		m_gammaData->LoadData(dybParameters::gammaData_file);
	}
	if (dybParameters::fitB12) {
		m_b12Data->LoadData(dybParameters::b12Data_file);
	}
	if (dybParameters::fitC11) {
		m_c11Data->LoadData(dybParameters::c11Data_file);
	}
	if (dybParameters::fitC10) {
		m_c10Data->LoadData(dybParameters::c10Data_file);
	}
	if (dybParameters::fitK40) {
		m_k40Data->LoadData(dybParameters::k40Data_file);
	}
	if (dybParameters::fitBi212) {
		m_bi212Data->LoadData(dybParameters::bi212Data_file);
	}
	if (dybParameters::fitBi214) {
		m_bi214Data->LoadData(dybParameters::bi214Data_file);
	}
	if (dybParameters::fitTl208) {
		m_tl208Data->LoadData(dybParameters::tl208Data_file);
	}
	if (dybParameters::fitLsLBNL) {
		m_lsDataLBNL->LoadData(dybParameters::lsData_file_LBNL);
	}
	if (dybParameters::fitLsIHEP) {
		m_lsDataIHEP->LoadData(dybParameters::lsData_file_IHEP);
	}
	if (dybParameters::fitFadc) {
		m_fadcData->LoadData(dybParameters::fadcData_file);
	}
}
void dybGlobalFit::LoadToyMC(int i){
	std::cout << " ---> Start loading data " << std::endl;
	stringstream ss;ss<<i;
	string toySuffix     = dybParameters::toyKey + "_" +ss.str() + ".dat";
	string gammaToyFile  = dybParameters::toyFolder+"gammaToy_" +toySuffix;
	string b12ToyFile    = dybParameters::toyFolder+"b12Toy_"   +toySuffix;
	string c11ToyFile    = dybParameters::toyFolder+"c11Toy_"   +toySuffix;
	string c10ToyFile    = dybParameters::toyFolder+"c10Toy_"   +toySuffix;
	string lsIHEPToyFile = dybParameters::toyFolder+"lsIHEPToy_"+toySuffix;
	string lsLBNLToyFile = dybParameters::toyFolder+"lsLBNLToy_"+toySuffix;
	string fadcToyFile   = dybParameters::toyFolder+"fadcToy_"  +toySuffix;
	//m_gammaData ->LoadData(gammaToyFile );
	//m_b12Data   ->LoadData(b12ToyFile   );
	//m_lsDataLBNL->LoadData(lsLBNLToyFile);
	//m_lsDataIHEP->LoadData(lsIHEPToyFile);
	//m_fadcData.  LoadData(fadcToyFile  );
}
void dybGlobalFit::GenToyMC(){
	//LoadData();
	std::cout << " ---> Start generating all toy MC data sets " << std::endl;
	//m_gammaData ->GenToyMC();
	//m_b12Data   ->GenToyMC();
	//m_lsDataLBNL->GenToyMC();
	//m_lsDataIHEP->GenToyMC();
	//m_fadcData  ->GenToyMC();
}
double dybGlobalFit::GetChi2(double maxChi2){
	m_chi2       = 0;
	m_chi2B12    = 0;
	m_chi2C11    = 0;
	m_chi2C10    = 0;
        m_chi2K40    = 0;
	m_chi2Gamma  = 0;
	m_chi2LsLBNL = 0;
	m_chi2LsIHEP = 0;
	m_chi2Fadc   = 0;
	m_chi2Michel = 0;
	m_chi2Alpha  = 0;
	
	if(dybParameters::fitGamma) {
                m_chi2Gamma  = m_gammaData->GetChi2();
                m_chi2      += m_chi2Gamma;
		m_chi2 += pow((dybGammaPeak::s_gamScale-dybParameters::gamScale)/dybParameters::gamScaleError,2);
                if(maxChi2>0 && m_chi2>maxChi2) return 10000;
        }
	if(dybParameters::fitFadc)   {
		m_chi2Fadc = m_fadcData->GetChi2();
		m_chi2    += dybParameters::FadcWeight*m_chi2Fadc;
	        m_chi2 += pow((dybFadcData::s_fadcNor-dybParameters::fadcNor)/dybParameters::fadcNorError,2);
	        m_chi2 += pow((dybFadcData::s_fadcRes-dybParameters::fadcRes)/dybParameters::fadcResError,2);
		if(maxChi2>0 && m_chi2>maxChi2) return 10000;
	}
        if(dybParameters::fitLsLBNL)   {
                m_chi2LsLBNL = m_lsDataLBNL->GetChi2();
                m_chi2    += dybParameters::lsLBNLWeight*m_chi2LsLBNL;
                if(maxChi2>0 && m_chi2>maxChi2) return 10000;
        }
	/*if(dybParameters::fitMichel)   {
		m_chi2Michel = m_michelData->GetChi2();
		m_chi2      += m_chi2Michel;
	}
	*/
	if(dybParameters::fitB12)   {
		m_chi2B12 = m_b12Data->GetChi2();
		m_chi2   += dybParameters::b12Weight*m_chi2B12;
	}
	if(dybParameters::fitC11)   {
		m_chi2C11 = m_c11Data->GetChi2();
		m_chi2   += dybParameters::c11Weight*m_chi2C11;
	}
	if(dybParameters::fitC10)   {
		m_chi2C10 = m_c10Data->GetChi2();
		m_chi2   += dybParameters::c10Weight*m_chi2C10;
	}
        if(dybParameters::fitK40)   {
                m_chi2K40 = m_k40Data->GetChi2();
                m_chi2   += dybParameters::k40Weight*m_chi2K40;
        }
	if(dybParameters::fitBi212)   {
		m_chi2Bi212 = m_bi212Data->GetChi2();
		m_chi2     += dybParameters::bi212Weight*m_chi2Bi212;
	}
	if(dybParameters::fitBi214)   {
		m_chi2Bi214 = m_bi214Data->GetChi2();
		m_chi2     += dybParameters::bi214Weight*m_chi2Bi214;
	}
	if(dybParameters::fitTl208)   {
		m_chi2Tl208 = m_tl208Data->GetChi2();
		m_chi2     += dybParameters::tl208Weight*m_chi2Tl208;
	}
	//std::cout << " m_chi2Gamma  = " << m_chi2Gamma  << std::endl;
	//std::cout << " m_chi2B12    = " << m_chi2B12    << std::endl;
	//std::cout << " m_chi2LsLBNL = " << m_chi2LsLBNL << std::endl;
	//std::cout << " m_chi2LsIHEP = " << m_chi2LsIHEP << std::endl;
	//std::cout << " m_chi2Fadc   = " << m_chi2Fadc  << std::endl;
	//std::cout << " m_chi2Michel = " << m_chi2Michel  << std::endl;
	if(dybParameters::constrainTau)	{
		if(dybEnergyModel::s_tau1>dybParameters::elecTauMax)
			m_chi2 += pow((dybParameters::elecTauMax-dybEnergyModel::s_tau1)/dybParameters::elecTauSigma,2);
		if(dybEnergyModel::s_tau2>dybParameters::elecTauMax)
			m_chi2 += pow((dybParameters::elecTauMax-dybEnergyModel::s_tau2)/dybParameters::elecTauSigma,2);
	}
        if(dybParameters::constrainFadc) {
                m_chi2 += pow((dybEnergyModel::s_alp1-dybParameters::alpha_start)/dybParameters::alphaError,2);
                m_chi2 += pow((dybEnergyModel::s_tau1-dybParameters::tau_start)/dybParameters::tauError,2);
        }

        if(dybParameters::fitK40)  m_chi2 += pow((dybSpectrum::s_k40Scale-dybParameters::k40Scale)/dybParameters::k40ScaleError,2);
	//std::cout << " ----> chi2 = " << m_chi2 << std::endl;
	return m_chi2;
}
double dybGlobalFit::GetReducedChi2(){
	int nDoF = 5;
	m_chi2Gamma  = m_gammaData ->GetChi2(nDoF);
	m_chi2B12    = m_b12Data   ->GetChi2(nDoF);
	m_chi2C11    = m_c11Data   ->GetChi2(nDoF);
	m_chi2C10    = m_c10Data   ->GetChi2(nDoF);
        m_chi2K40    = m_k40Data   ->GetChi2(nDoF);
	m_chi2LsLBNL = m_lsDataLBNL->GetChi2(nDoF);
	m_chi2LsIHEP = m_lsDataIHEP->GetChi2(nDoF);
	m_chi2Fadc   = m_fadcData  ->GetChi2(nDoF);
	//m_chi2Michel = m_michelData->GetChi2(nDoF);
	int nData = 0;
	if(dybParameters::fitGamma ) nData += m_gammaData -> GetNData();
	if(dybParameters::fitB12   ) nData += m_b12Data   ->GetNData();
	if(dybParameters::fitC11   ) nData += m_c11Data   ->GetNData();
	if(dybParameters::fitC10   ) nData += m_c10Data   ->GetNData();
        if(dybParameters::fitK40   ) nData += m_k40Data   ->GetNData();
	if(dybParameters::fitLsLBNL) nData += m_lsDataLBNL->GetNData();
	if(dybParameters::fitLsIHEP) nData += m_lsDataIHEP->GetNData();
	if(dybParameters::fitFadc  ) nData += m_fadcData  ->GetNData();
	//if(dybParameters::fitMichel) nData += m_fadcData  ->GetNData();
	m_chi2MinRed = m_chi2Min / double(nData-nDoF);
}
void dybGlobalFit::Fit(){
	m_nParameter = 13;
	m_minuit = new TMinuit (m_nParameter);
	m_minuit->SetPrintLevel(dybParameters::fitPrintLevel);
	m_minuit->SetFCN(ChisqFCN);
	
	double arglist[13];
	int ierrflag = 0;

	m_minuit->mnexcm("CLEAR", arglist, 0, ierrflag);
	m_minuit->mnparm(0, "scale", dybParameters::p0_start, 0.001,0.5,2.0, ierrflag);
	string scintPar[3] = {"kB","kC","Radiation"};
	double parMin  [3] ={0};
	double parMax  [3] ={0};
	double stepSize[3] ={0};
	if(dybParameters::scintillatorParametrization==kPhysics)
	{
		//scintPar[0] = "kB";stepSize[0]=0.1;parMin[0]=4.0;parMax[0]=24.9;
		scintPar[0] = "kB";stepSize[0]=0.1;parMin[0]=4.0;parMax[0]=24.8;
		scintPar[1] = "kC";stepSize[1]=0.01;parMin[1]=0;parMax[1]=10;
		scintPar[2] = "kR";stepSize[2]=0.1;parMin[2]=0;parMax[2]=1;
	}
	if(dybParameters::scintillatorParametrization==kLowECorrEmpirical
	 ||dybParameters::scintillatorParametrization==kSimpleEmpirical)
	{
		scintPar[0] = "p1";stepSize[0]=0.1;parMin[0]=0;parMax[0]=10;
		scintPar[1] = "p2";stepSize[1]=0.01;parMin[1]=0;parMax[1]=10;
		scintPar[2] = "p3";stepSize[2]=0.1;parMin[2]=-1;parMax[2]=1;
	}
	m_minuit->mnparm(1,scintPar[0].c_str(), dybParameters::p1_start, 0.1,  parMin[0],parMax[0],ierrflag);
        m_minuit->mnparm(2,scintPar[1].c_str(), dybParameters::p2_start, 0.01,  parMin[1],parMax[1],ierrflag);
	m_minuit->mnparm(3,"alpha"            , dybParameters::alpha_start, 0.001, 0, 0.3, ierrflag);
	m_minuit->mnparm(4,"tau"              , dybParameters::tau_start,   0.001,  0, 300, ierrflag);
	m_minuit->mnparm(5,"n12Ratio",dybParameters::n12Ratio,0.1*dybParameters::n12RatioError,0,0.1,ierrflag);
	m_minuit->mnparm(6,"gamScale",dybParameters::gamScale,0.1*dybParameters::gamScaleError,0.5,1.5,ierrflag);
        m_minuit->mnparm(7,"fadcNor",dybParameters::fadcNor,0.001,0.9,1.1,ierrflag);
        m_minuit->mnparm(8,"fadcRes",dybParameters::fadcRes,0.001,-0.2,0.2,ierrflag);
        m_minuit->mnparm(9,"lsScale",dybParameters::lsScale_start,0.001,0.5,2.0,ierrflag);
        m_minuit->mnparm(10,"k40Scale",dybParameters::k40Scale_start,0.1*dybParameters::k40ScaleError,0.5,1.5,ierrflag);
        m_minuit->mnparm(11,"c10C11Frac",dybParameters::c10C11Frac_start,0.01,0.,1.,ierrflag);
        m_minuit->mnparm(12,"c10Be11Frac",dybParameters::c10Be11Frac_start,0.005,0.,1.,ierrflag);
	
	if(dybParameters::fixScintP0 ) m_minuit->FixParameter(0);// absolute energy scale
	if(dybParameters::fixScintP1 ) m_minuit->FixParameter(1);
	if(dybParameters::fixScintP2 ) m_minuit->FixParameter(2);
	if(dybParameters::fixElecP0  ) m_minuit->FixParameter(3);
	if(dybParameters::fixElecP1  ) m_minuit->FixParameter(4);
	if(dybParameters::fixN12     ) m_minuit->FixParameter(5);
	if(dybParameters::fixGamScale) m_minuit->FixParameter(6);
        if(dybParameters::fixFadcNor     ) m_minuit->FixParameter(7);
        if(dybParameters::fixFadcRes) m_minuit->FixParameter(8);
        if(dybParameters::fixLsScale ) m_minuit->FixParameter(9);
        if(dybParameters::fixK40Scale ) m_minuit->FixParameter(10);
	/*
	if(dybParameters::electronicsParametrization != kDoubleExponential) 
	{
		m_minuit->FixParameter(6);
		m_minuit->FixParameter(7);
	}
	*/
	if(!dybParameters::fitB12) m_minuit->FixParameter(5);
 	if(!dybParameters::fitGamma) m_minuit->FixParameter(6);
        if(!dybParameters::fitFadc) m_minuit->FixParameter(7);
        if(!dybParameters::fitFadc) m_minuit->FixParameter(8);
	if(!dybParameters::fitC10) {
		m_minuit->FixParameter(11);
		m_minuit->FixParameter(12);
	}
	
	m_nParameter = m_minuit->GetNumPars();
        cout<<"Check m_minuit->GetNumPars()="<<m_minuit->GetNumPars()<<endl;
	double err = 0;
	for (int i = 0; i < m_nParameter; i++)
		m_minuit->GetParameter(i, m_parameters[i], err);
	SetParameters();
	// Minimization strategy
	// 1 standard;	2 try to improve minimum (slower)
	arglist[0] = 1;
	m_minuit->mnexcm("SET STR", arglist, 1, ierrflag);
	// Printf("	 SET STRategy	<level>");
	// Printf("		Sets the strategy to be used in calculating first and second");
	// Printf("		derivatives and in certain minimization methods.");
	// Printf("		In general, low values of <level> mean fewer function calls");
	// Printf("		and high values mean more reliable minimization.");
	// Printf("		Currently allowed values are 0, 1 (default), and 2.");
	arglist[0] = 2000000; //maxCalls;
	arglist[1] = 1E-2; //tolerance; 

 	m_minuit->mnexcm("MIGrad", arglist, 2, ierrflag);
	//m_minuit->mnexcm("SIMPLEX ", arglist, 2, ierrflag);
	 //arglist[0] = 0; 
	//m_minuit->mnexcm("SCAN ", arglist, 2, ierrflag);

	double min, edm, errdef;
	int nvpar, nparx, icstat;
	m_minuit->mnstat(m_chi2Min, edm, errdef, nvpar, nparx, icstat);
	// void mnstat(Double_t &fmin, Double_t &fedm, Double_t &errdef, Int_t &npari, Int_t &nparx, Int_t &istat)
	// Returns concerning the current status of the minimization*-*-*-*-*
	// User-called
	//			 Namely, it returns:
	//			FMIN: the best function value found so far
	//			FEDM: the estimated vertical distance remaining to minimum
	//			ERRDEF: the value of UP defining parameter uncertainties
	//				NPARI: the number of currently variable parameters
	//			NPARX: the highest (external) parameter number defined by user
	//			ISTAT: a status integer indicating how good is the covariance
	//					 matrix:	0= not calculated at all
	//										1= approximation only, not accurate
	//										2= full matrix, but forced positive-definite
	//										3= full accurate covariance matrix
	//for(int i=0; i<dybParameters::nFitParameter; i++)
	for(int i=0; i<m_nParameter; i++)
	{
		m_minuit->GetParameter(i, m_bestFit[i], m_bestFitError[i]);
		//cout<<"curvalue: "<<curvalue<<"	curerror: "<<curerror<<endl;
	}
	for (int i = 0; i < m_nParameter; i++)
		m_parameters[i] = m_bestFit[i];
	SetParameters();  

	//m_nFreeParameter = m_minuit->GetNumFreePars() - 2;
	m_nFreeParameter = 5;
	m_nFitParameter = m_minuit->GetNumFreePars()-2;
        cout<<"Check m_nFreeParameter = m_minuit->GetNumFreePars()-2="<<m_nFreeParameter<<endl;
//	//m_minuit->mnemat(&m_covMatrix[0][0],m_nFreeParameter);
	m_minuit->mnemat(&m_covMatrix[0][0],m_nParameter);
//	/// draw 1-sigma contout
//	////m_minuit->SetErrorDef(4);
//	////TGraph* contour2Sigma = (TGraph*)m_minuit->Contour(80,1,1);
//	////contour2Sigma->SetFillColor(kBlue-7);
//	m_minuit->SetErrorDef(1);
//	TGraph* contour1Sigma = (TGraph*)m_minuit->Contour(80,1,2);
//	contour1Sigma->SetFillColor(kRed-7);
//	TCanvas* contourCanvas = new TCanvas("contourCanvas","",800,520);
//	////contour2Sigma->Draw("alf");
//	contour1Sigma->Draw("alf");
//	TFile* contFile = new TFile("contour.root","recreate");
//	contour1Sigma->Write("1sigma");
//	////contour2Sigma->Write("2sigma");
//	contFile->Close();
//	contourCanvas->SaveAs("plots/contour.pdf");
//	delete contourCanvas;
//    	DrawErrors();
	
	delete m_minuit;
	m_minuit = 0;
	std::cout << " =============================== " << std::endl;
	std::cout << " chi2 minimum: " << m_chi2Min << std::endl;
	std::cout << " =============================== " << std::endl;
	if(dybParameters::doFullAnalysis) WriteResult();
}
void dybGlobalFit::WriteResult(){
	string resultpath = "output/results/";
	TString matName = resultpath+"matrix_" + dybParameters::toyKey + ".dat";
	ofstream matFile(matName);
	//std::cout << " ****> " << m_nFreeParameter << std::endl;
	//for (int i = 0; i < m_nFreeParameter; i++)
	for (int i = 0; i < m_nFitParameter; i++)
	{
		//std::cout << " i = " << i << std::endl;
		//for (int j = 0; j < m_nFreeParameter; j++)
		for (int j = 0; j < m_nFitParameter; j++)
		{
			//std::cout << m_covMatrix[i][j] << " ";
			matFile << m_covMatrix[i][j] << " ";
		}
		//std::cout << std::endl;
		matFile << std::endl;
	}
	TString bestFitName = resultpath+"bestFit_" + dybParameters::toyKey + ".dat";
	ofstream bestFitFile(bestFitName);
	bestFitFile << m_chi2Min << " " << 0 << std::endl;
	for (int i = 0; i < m_nParameter; i++)
	{
		bestFitFile << m_bestFit[i] << " " << m_bestFitError[i] << std::endl;
	}
	std::cout << " m_chi2B12    = " << m_chi2B12    << std::endl;
	std::cout << " m_chi2C11    = " << m_chi2C11    << std::endl;
	std::cout << " m_chi2C10    = " << m_chi2C10    << std::endl;
	GetReducedChi2();
	TString chi2Name = resultpath+"chi2_" + dybParameters::toyKey + ".dat";
	ofstream chi2File(chi2Name);
	chi2File << "TotChi2 " << m_chi2Min    << std::endl;
	chi2File << "RedChi2 " << m_chi2MinRed << std::endl;
	chi2File << "Gamma   " << m_chi2Gamma  << std::endl;
	chi2File << "B12     " << m_chi2B12    << std::endl;
	chi2File << "C11     " << m_chi2C11    << std::endl;
	chi2File << "C10     " << m_chi2C10    << std::endl;
        chi2File << "K40     " << m_chi2K40    << std::endl;
	chi2File << "lsLBNL  " << m_chi2LsLBNL << std::endl;
	chi2File << "lsIHEP  " << m_chi2LsIHEP << std::endl;
	chi2File << "FADC    " << m_chi2Fadc   << std::endl;
	std::cout << " =====> Reduced Chi2 " << std::endl;
	std::cout << "TotChi2 " << m_chi2Min    << std::endl;
	std::cout << "RedChi2 " << m_chi2MinRed << std::endl;
	std::cout << "Gamma   " << m_chi2Gamma  << std::endl;
	std::cout << "B12     " << m_chi2B12    << std::endl;
	std::cout << "C11     " << m_chi2C11    << std::endl;
	std::cout << "C10     " << m_chi2C10    << std::endl;
        std::cout  << "K40     " << m_chi2K40    << std::endl;
	std::cout << "lsLBNL  " << m_chi2LsLBNL << std::endl;
	std::cout << "lsIHEP  " << m_chi2LsIHEP << std::endl;
	std::cout << "FADC    " << m_chi2Fadc   << std::endl;
	std::cout << std::endl;
}
void dybGlobalFit::LoadResult(string name) {
	m_nParameter = 13;
	string filename = "output/results/bestFit_"+name+".dat";
	//string filename = "run/output/results/bestFit_"+name+".dat";
	std::cout << " Loading " << filename << std::endl;
	ifstream bestFitfile(filename.c_str());
	double bestFit,bestFitE;
	int parIdx=-1;
	//int m_nFreeParameter = 0;
	//std::cout << " ================> " << std::endl;
	while (bestFitfile >> bestFit >> bestFitE )
	{
		if(parIdx==-1) m_chi2Min = bestFit;
		m_bestFit     [parIdx]  = bestFit;
		m_bestFitError[parIdx]  = bestFitE;
		//if(bestFitE>0 && parIdx<8) m_nFreeParameter++;
		parIdx++;
	}
        cout<<"Check running dybGlobalFit::LoadResult!!!  m_nFreeParameter="<<m_nFreeParameter<<endl;
	filename = "output/results/matrix_"+name+".dat";
	//filename = "run/output/results/matrix_"+name+".dat";
	ifstream covMatfile(filename.c_str());
	
	for (int i = 0; i < m_nParameter; i++)
	{
		for (int j = 0; j < m_nParameter; j++)
		{
			if(m_bestFitError[i]==0 || m_bestFitError[j]==0)
				m_covMatrix[i][j] = 0;
			else
				covMatfile >> m_covMatrix[i][j];
			
			//std::cout << m_covMatrix[i][j] << " ";
		}
		//std::cout << std::endl;
	}
	for (int i = 0; i < m_nParameter; i++)
		m_parameters[i] = m_bestFit[i];
	SetParameters();
}
void dybGlobalFit::SetParameters(){
	dybEnergyModel::SetScintP0(m_parameters[0]);
	dybEnergyModel::SetScintP1(m_parameters[1]);
	dybEnergyModel::SetScintP2(m_parameters[2]);
	dybEnergyModel::SetElecP0 (m_parameters[3]);
	dybEnergyModel::SetElecP1 (m_parameters[4]);
	dybSpectrum ::s_n12Ratio = m_parameters[5];
	dybGammaPeak::s_gamScale = m_parameters[6];
        dybFadcData::s_fadcNor = m_parameters[7];
	dybFadcData::s_fadcRes = m_parameters[8];
        dybLSData::s_lsScale = m_parameters[9];
        dybSpectrum::s_k40Scale = m_parameters[10];
        dybSpectrum::s_c10C11Frac = m_parameters[11];
        dybSpectrum::s_c10Be11Frac = m_parameters[12];
        dybSpectrum::s_b12Branch0 = dybParameters::b12Branch0;
        dybSpectrum::s_b12Branch1 = dybParameters::b12Branch1;
        dybSpectrum::s_b12Branch2 = dybParameters::b12Branch2;
        dybSpectrum::s_n12Branch0 = dybParameters::n12Branch0;
        dybSpectrum::s_n12Branch1 = dybParameters::n12Branch1;
        dybSpectrum::s_n12Branch2 = dybParameters::n12Branch2;
        dybSpectrum::s_n12Branch3 = dybParameters::n12Branch3;
        dybSpectrum::s_n12Branch4 = dybParameters::n12Branch4;
  	
}
void dybGlobalFit::SetParameters(Double_t *par){
	for (int i = 0; i < m_nParameter; i++)
		m_parameters[i] = par[i];
    SetParameters();
}
void dybGlobalFit::SetFreePar(Double_t *par){
	for (int i = 0; i < 5; i++)
		m_parameters[i] = par[i];
    SetParameters();
}
/*
void dybGlobalFit::SetFreePar(Double_t A, Double_t kB, Double_t kC, Double_t alpha, Double_t tau){
    m_parameters[0] = A;
    m_parameters[1] = kB;
    m_parameters[2] = kC;
    m_parameters[3] = alpha;
    m_parameters[4] = tau;
    SetParameters();
}
*/
void dybGlobalFit::SetParameter(Int_t ipar, Double_t value){
    m_parameters[ipar] = value;
    SetParameters();
}
void dybGlobalFit::ChisqFCN(Int_t &npar, Double_t *grad, Double_t &fval, Double_t *par, Int_t flag){
	double err = 0;
	for (int i = 0; i < m_nParameter; i++){
		if(m_minuit)
			m_minuit->GetParameter(i, m_parameters[i], err);
		else
			m_parameters[i] = par[i];
	}
	SetParameters();
	fval = GetChi2();
}
void dybGlobalFit::SetError(int parNo,int sign){
	std::cout << " ========= "<< parNo << " ========" << std::endl;
	cout<<"Check running dybGlobalFit::SetError!!!  m_nParameter="<<m_nParameter<<endl;
	for (int parIdx=0; parIdx<m_nParameter;parIdx++)
	{
		m_parameters[parIdx] = m_bestFit[parIdx];
		if(m_covMatrix[parNo][parNo]<0.00000001) continue;
		//if(parIdx!=0) continue;
		//if(parIdx==parNo)
		//{
			//m_parameters[parIdx] += sign*sqrt(m_covMatrix[parIdx][parIdx]);
			//std::cout << " parE = " << sign*sqrt(m_covMatrix[parIdx][parIdx]) << std::endl;
		//}
			////par[parIdx] += sign*bestFitE[parIdx];
		//else 
			m_parameters[parIdx] += sign*m_covMatrix[parNo][parIdx]/sqrt(m_covMatrix[parNo][parNo]);
			std::cout << " ----- "<< m_parameters[parIdx] << std::endl;

			//m_parameters[parIdx] += sign*bestFitE[parIdx];
			//par[parIdx] += sign*1.5;
	}
	//if(m_parameters[0]>20) m_parameters[0]=20;
	//for (int i = 0; i < 6; i++)
	//{
		//std::cout << " par = " << par[i] << std::endl;
	//}
	SetParameters();
}
void dybGlobalFit::GetCLSample(){
	double deltaChi2 = GetDeltaChi2();
	double chi2=10000;
	int iTry = 0;
	while(chi2>m_chi2Min+deltaChi2)
	{
		for (int parIdx = 0; parIdx < m_nParameter; parIdx++)
		{
			//std::cout << " best = " << m_bestFit[parIdx] << ", err = " << m_bestFitError[parIdx] << std::endl;
			m_parameters[parIdx] = m_bestFit[parIdx] + (m_rand.Rndm()-0.5)*2.5*m_bestFitError[parIdx];
			//if(parIdx<5) m_parameters[parIdx] = m_bestFit[parIdx];//for noNuisance 20190121
			//std::cout << " par " << parIdx << " = " << m_parameters[parIdx] << std::endl;
		}
		SetParameters();
		chi2 = GetChi2(m_chi2Min+deltaChi2);
		if(chi2<=m_chi2Min+deltaChi2)
		{
			//std::cout << " deltaChi2 = " << chi2-m_chi2Min << " with " << iTry << " shots " << chi2 << std::endl;
		}
		iTry++;
	}
	return;
}
void dybGlobalFit::DrawErrors(){
	std::cout << "Check  m_nParameter = " << m_nParameter << std::endl;
	LoadResult(dybParameters::toyKey);
	std::cout << " --> Computing errors for " << m_nFreeParameter << " free parameters" << std::endl;
	std::cout << " --> Scan for delta chi2 = " << GetDeltaChi2() << std::endl;
	//for (int i = 0; i < m_nParameter; i++)
	//{
		//for (int j = 0; j < m_nParameter; j++)
			//std::cout << m_covMatrix[i][j] << " ";
		//std::cout << std::endl;
	//}
	int nSamples = 500;
	for (int i = 0; i < m_nParameter; i++)
		m_parameters[i] = m_bestFit[i];
	
	SetParameters();
	
	std::cout << " *****************&&&&&******* " << std::endl;
	std::cout << " *****************&&&&&******* " << std::endl;
	cout << dybEnergyModel::s_p0    << endl;
	cout << dybEnergyModel::s_p1    << endl;
	cout << dybEnergyModel::s_p2    << endl;
	cout << dybEnergyModel::s_alp1  << endl;
	cout << dybEnergyModel::s_tau1  << endl;
	cout << dybSpectrum ::s_n12Ratio << endl;
	cout << dybGammaPeak::s_gamScale << endl;
        cout << dybFadcData::s_fadcNor << endl;
	cout << dybFadcData::s_fadcRes << endl;
        cout << dybLSData::s_lsScale << endl;
        cout << dybSpectrum::s_k40Scale << endl;
        cout << dybSpectrum ::s_c10C11Frac << endl;
        cout << dybSpectrum ::s_c10Be11Frac << endl;
	
	TGraph bestFitNL = dybEnergyModel::DrawPositronFullNL(nSamples);

	m_bestFitNL     = dybEnergyModel::SamplePositronFullNL(nSamples);
	m_bestFitNLHigh = dybEnergyModel::SamplePositronFullNL(nSamples);
	m_bestFitNLLow  = dybEnergyModel::SamplePositronFullNL(nSamples);

	string errorName = "output/errors/errors_"+dybParameters::toyKey+".root";
	TFile* testFile =  new TFile(errorName.c_str(),"recreate");
	//string birksSigmaName = "birksSigma_"+dybParameters::toyKey+".dat";
	//ofstream birksSigmaFile(birksSigmaName.c_str());
	/// -- compute 1-sigma uncertainty band ---
	for (int idx = 0; idx < m_contourNItr; idx++)
	{
		GetCLSample();
		vector<double> thisNL = dybEnergyModel::SamplePositronFullNL(nSamples);
		//vector<double> thisNL = dybEnergyModel::SampleElectronFullNL(nSamples);
		//ector<double> thisNL = dybEnergyModel::SampleElectronicsNL(nSamples);
		//birksSigmaFile << m_chi2 - m_chi2Min << " " << dybEnergyModel::s_p0 << dybEnergyModel::GetKB() << " " << dybEnergyModel::s_cer << " " << dybEnergyModel::s_alp1 << dybEnergyModel::s_tau1 << endl;
		for (int i=0; i<thisNL.size(); i++)
		{
			if(thisNL[i]>m_bestFitNLHigh[i]) {m_bestFitNLHigh[i] = thisNL[i];}
			if(thisNL[i]<m_bestFitNLLow [i]) {m_bestFitNLLow [i] = thisNL[i];}
		}
		std::cout << " =============> " << idx << " out of " << m_contourNItr << std::endl;
		stringstream ss;ss<<idx;
		TGraph curveG = dybEnergyModel::DrawPositronFullNL(nSamples);
		TString name = "curve_"+ss.str();
		testFile->cd();
		curveG.Write(name);
	}
	/// -----------------------------------
	TGraphAsymmErrors* nlBand = new TGraphAsymmErrors(0);
	for (int i=0; i<m_bestFitNL.size(); i++)
	{
		double energy,nl;
		bestFitNL.GetPoint(i,energy,nl);
		nlBand->SetPoint(i,energy,nl);
		nlBand->SetPointEXhigh(i,0);
		nlBand->SetPointEXlow (i,0);
		nlBand->SetPointEYlow (i,m_bestFitNLHigh[i]-nl);
		nlBand->SetPointEYhigh(i,nl-m_bestFitNLLow[i]);
	}
	testFile->cd();
	nlBand->Write("nominal");
	testFile->Close();
	delete testFile;
}
double dybGlobalFit::GetDeltaChi2() {
	cout<<"Check running dybGlobalFit::GetDeltaChi2()!!!"<<"  m_nFreeParameter="<<m_nFreeParameter<<endl;
	if(m_nFreeParameter==1)  return 1.07 ;
	if(m_nFreeParameter==2)  return 2.41 ;
	if(m_nFreeParameter==3)  return 3.67 ;
	if(m_nFreeParameter==4)  return 4.88 ;
	if(m_nFreeParameter==5)  return 6.06 ;
	if(m_nFreeParameter==6)  return 7.23 ;
	if(m_nFreeParameter==7)  return 8.38 ;
	if(m_nFreeParameter==8)  return 9.52 ;
	if(m_nFreeParameter==9)  return 10.66;
	if(m_nFreeParameter==10) return 11.78;
	if(m_nFreeParameter==11) return 12.88;
	return 10;
}
void dybGlobalFit::Plot() {

	m_gammaData ->Plot(true);
	m_b12Data   ->Plot(true);
	m_c11Data   ->Plot(true);
	m_c10Data   ->Plot(true);
	return;
        m_k40Data   ->Plot(true);
	m_bi212Data ->Plot(true);
	m_bi214Data ->Plot(true);
	m_tl208Data ->Plot(true);
	m_lsDataLBNL->Plot(true);
	m_lsDataIHEP->Plot(true);
        std::cout<<"Running dybGlobalFit::Plot()!!! m_fadcData->Plot(true)!!!"<<std::endl;
	m_fadcData->Plot(true);
	//m_michelData->Plot(true);
	//m_alphaData ->Plot(true);
	
	stringstream ssLsIhep;ssLsIhep.precision(3);ssLsIhep<<m_chi2LsIHEP;
	stringstream ssLsLbnl;ssLsLbnl.precision(3);ssLsLbnl<<m_chi2LsLBNL;
	TGraphErrors lsIHEP = m_lsDataIHEP->Plot();
	TGraphErrors lsLBNL = m_lsDataLBNL->Plot();
        TGraphErrors fadcData = m_fadcData->Plot();
	TString lsTitle = "Benchtop LS Data: #chi^{2}_{IHEP} = "+ssLsIhep.str()+", #chi^{2}_{LBNL} = "+ssLsLbnl.str();
	lsIHEP.SetTitle(lsTitle);
	lsLBNL.SetMarkerStyle(20);
	//lsLBNL.SetMarkerSize(1.2);
	lsLBNL.SetLineWidth(2);
	lsLBNL.SetMarkerSize(1);
	lsLBNL.SetMarkerColor(kBlue-2);
	lsLBNL.SetLineColor  (kBlue-2);
	lsIHEP.SetMarkerStyle(20);
	lsIHEP.SetMarkerSize(1.1);
	//lsIHEP.SetMarkerColor(kBlue-5);
	//lsIHEP.SetLineColor  (kBlue-5);
	lsIHEP.SetMarkerColor(kBlue-2);
	lsIHEP.SetLineColor  (kBlue-2);
	TCanvas* lsC = new TCanvas("lsC","",800,520);
	lsIHEP.Draw("APZ");
	lsLBNL.DrawClone("PZ");
	lsLBNL.SetMarkerStyle(20);
	lsLBNL.SetMarkerColor(kWhite);
	lsLBNL.SetMarkerSize(0.5);
	lsLBNL.Draw("PZ");
	//for (int i=0;i<lsLBNL.GetN();i++)
	//{
		//double energy,nl;
		//lsLBNL.GetPoint(i,energy,nl);
		//lsLBNL.SetPoint(i,energy,nl*1.0);
	//}
	
	lsLBNL.GetXaxis()->SetLimits(0,1.2);
	//lsLBNL.GetYaxis()->SetRangeUser(0.7,1.1);
	//lsLBNL.GetYaxis()->SetRangeUser(0.75,1.1);
	lsLBNL.GetYaxis()->SetRangeUser(0.75,1.1);
	//lsLBNL.GetYaxis()->SetRangeUser(0.95,1.06);
	//lsLBNL.Draw("APZ");
	TLegend* legLS = new TLegend(0.58,0.16,0.88,0.4);
	legLS->SetBorderSize(0);
	legLS->SetFillColor(-1);
	TLegendEntry *leIHEP = legLS->AddEntry((TObject*)0,"IHEP Data","PE");
	TLegendEntry *leLBNL = legLS->AddEntry((TObject*)0,"LBNL Data","PE");
	//TLegendEntry *leLBNL = legLS->AddEntry((TObject*)0,"NuWa quenching curve","PE");
	//TLegendEntry *leFit  = legLS->AddEntry((TObject*)0,"Best Fit Model","L");
	TLegendEntry *leFit  = legLS->AddEntry((TObject*)0,"Standalone best fit","L");
	leIHEP->SetMarkerStyle(20);
	leIHEP->SetMarkerSize(1.1);
	leIHEP->SetMarkerColor(kBlue-5);
	leIHEP->SetLineColor  (kBlue-5);
	leLBNL->SetMarkerStyle(20);
	leLBNL->SetMarkerSize(1.2);
	leLBNL->SetMarkerColor(kBlue-2);
	leLBNL->SetLineColor  (kBlue-2);
	leFit ->SetLineColor(kRed-2);
	leFit ->SetLineWidth(2);
	legLS->SetTextSize(0.04);
	legLS->Draw();
	TLegend* legLS2 = new TLegend(0.58,0.16,0.88,0.4);
	legLS2->SetBorderSize(0);
	legLS2->SetFillColor(-1);
	legLS2->SetFillStyle(-1);
	TLegendEntry *leIHEP2 = legLS2->AddEntry((TObject*)0," "," ");
	TLegendEntry *leLBNL2 = legLS2->AddEntry((TObject*)0," ","P");
	legLS2->AddEntry((TObject*)0 ," "," ");
	leIHEP2->SetMarkerStyle(20);
	leIHEP2->SetMarkerSize(1.2);
	leIHEP2->SetMarkerColor(kGray+3);
	leIHEP2->SetLineColor(kGray+3);
	//leIHEP->SetTextColor(kBlue+2);
	leLBNL2->SetMarkerStyle(20);
	leLBNL2->SetMarkerSize(0.5);
	leLBNL2->SetMarkerColor(kWhite);
	leLBNL2->SetLineColor(kWhite);
	//leLBNL->SetTextColor(kGreen+3);
	legLS2->SetTextSize(0.04);
	legLS2->Draw();
	string name = "plots/"+dybParameters::toyKey+"_LS"+"."+dybParameters::plotFormat;
	lsC->SaveAs(name.c_str());
        
	TGraph bestFitNL  = dybEnergyModel::DrawPositronFullNL(10000);
	TGraph gammaNL    = dybEnergyModel::DrawGammaFullNL   (10000);
	TGraph electronNL = dybEnergyModel::DrawElectronFullNL(10000);
	gammaNL.SetLineColor(kBlack);
	gammaNL.SetLineWidth(2);
	electronNL.SetLineWidth(2);
	gammaNL.SetLineStyle(2);
	bestFitNL.SetFillColor(kRed-8);
	bestFitNL.SetFillStyle(3144);
	bestFitNL.SetLineColor(kRed-2);
	bestFitNL.SetLineWidth(2);
	TString nameToy = dybParameters::toyKey;
}

