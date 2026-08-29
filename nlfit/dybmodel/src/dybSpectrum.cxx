#include "dybSpectrum.h"
#include "TROOT.h"

double dybSpectrum::s_n12Ratio = 0.04;
double dybSpectrum::s_c10C11Frac = 0.15;
double dybSpectrum::s_c10Be11Frac = 0.02;
double dybSpectrum::s_k40Scale = 1.0;

double dybSpectrum::s_b12Branch0 = 0.982780;
double dybSpectrum::s_b12Branch1 = 0.011820;
double dybSpectrum::s_b12Branch2 = 0.005400;
double dybSpectrum::s_n12Branch0 = 0.962835;
double dybSpectrum::s_n12Branch1 = 0.019003;
double dybSpectrum::s_n12Branch2 = 0.014117;
double dybSpectrum::s_n12Branch3 = 0.004045;
double dybSpectrum::s_n12Branch4 = 0.0;
double dybSpectrum::s_b12branch0WM = 0.0048;
double dybSpectrum::s_b12branch1WM = 0.0048;
double dybSpectrum::s_b12branch2WM = 0.0048;
double dybSpectrum::s_n12branch0WM = 0.0048;
double dybSpectrum::s_n12branch1WM = 0.0048;
double dybSpectrum::s_n12branch2WM = 0.0048;
double dybSpectrum::s_n12branch3WM = 0.0048;
double dybSpectrum::s_n12branch4WM = 0.0048;
double dybSpectrum::s_gausTable[s_nGausTable];
bool   dybSpectrum::s_gausTableReady = false;
std::vector<dybGammaPeak> dybSpectrum::s_gammaPeaks;

dybSpectrum::dybSpectrum(int nMaxBins,
												 int nMaxBinsData,  
												 int nMaxBr,  
												 int nMaxGam) 
{
	std::cout << " nMaxBins     = " << nMaxBins << std::endl;
	std::cout << " nMaxBinsData = " << nMaxBinsData << std::endl;
	std::cout << " nMaxBr       = " << nMaxBr << std::endl;
	std::cout << " nMaxGam      = " << nMaxGam << std::endl;
	
	m_nBins     = nMaxBins;
	m_nBinsData = nMaxBinsData;
	m_nBr       = nMaxBr;
	m_nGam      = nMaxGam;
	m_lastNormScale = 1.0;
	m_eMaxDraw  = 0.0;
	
	m_binCenter = new double[nMaxBins];
	m_eVis      = new double[nMaxBins];
	m_eVisBck   = new double[nMaxBins];
	m_eRec      = new double[nMaxBins];
	m_eRecBck   = new double[nMaxBins];
	m_eTheo     = new double[nMaxBinsData];
	m_eData     = new double[nMaxBinsData];
	m_eDataErr  = new double[nMaxBinsData];
	
	m_eTru      = new double*[nMaxBr];
	m_eTruBck   = new double*[nMaxBr];
	
	m_eTruAlp   = new double [nMaxBr];
	
	for (int branchIdx = 0; branchIdx < nMaxBr; branchIdx++)
	{
		m_eTru   [branchIdx] = new double[nMaxBins];
		m_eTruBck[branchIdx] = new double[nMaxBins];
	}
	m_eTruGam   = new double*[nMaxBr];
	for (int branchIdx = 0; branchIdx < nMaxBr; branchIdx++)
	{
		m_eTruGam[branchIdx] = new double[nMaxGam];
	}
}
dybSpectrum::~dybSpectrum() 
{
	std::cout << " Destroying " << m_name << " <------" << std::endl;
	for (int branchIdx = 0; branchIdx < m_nBr; branchIdx++)
	{
		delete [] m_eTru   [branchIdx];
		delete [] m_eTruBck[branchIdx];
	}
	for (int branchIdx = 0; branchIdx < m_nBr; branchIdx++)
	{
		delete [] m_eTruGam[branchIdx];
	}
	delete [] m_binCenter;
	delete [] m_eVis     ;
	delete [] m_eVisBck  ;
	delete [] m_eRec     ;
	delete [] m_eRecBck  ;
	delete [] m_eTheo    ;
	delete [] m_eData    ;
	delete [] m_eDataErr ;
	delete [] m_eTru     ;
	delete [] m_eTruBck  ;
	delete [] m_eTruGam  ;
	delete [] m_eTruAlp  ;
}
void dybSpectrum::LoadData(string fileName)
{
	m_opt          = true;
	m_dataIsLoaded = false;
	if(s_gammaPeaks.size()==0)
	{
		AddGamma("0.2MeV","hE1", 0.2);  
		AddGamma("0.4MeV","hE3", 0.4);  
		AddGamma("0.6MeV","hE5", 0.6);  
		AddGamma("0.8MeV","hE7", 0.8);  
		AddGamma("1MeV",  "hE9", 1.0);  
		AddGamma("2MeV",  "hE10",2.0);  
		AddGamma("3MeV",  "hE11",3.0);  
		AddGamma("4MeV",  "hE12",4.0);  
		AddGamma("5MeV",  "hE13",5.0);  
	}
	PrepGaus     ();
	SetParameters();
	cout << " ---> Preparing " << m_name << " data " << endl;
	
	m_binWidth  = (m_eMax-m_eMin)/double(m_nBins);
	m_fitMinBin = int((m_fitMin-m_eMin)/m_binWidth);
	m_fitMaxBin = int((m_fitMax-m_eMin)/m_binWidth);

	for(int branchIdx=0; branchIdx<m_nBr; branchIdx++)
	{
		for(int i=0; i<m_nBins; i++)
		{
			m_binCenter[i] = m_eMin + m_binWidth*(i+0.5);
			m_eTru   [branchIdx][i] = 0;
			m_eTruBck[branchIdx][i] = 0;
		}
		for(int gamIdx=0; gamIdx<m_nGam; gamIdx++)
		{
			m_eTruGam[branchIdx][gamIdx] = 0;
		}
		m_eTruAlp[branchIdx] = 0;
	}
	InitTheo();
    cout<<m_name<<" theo hist prepared."<<endl;
	if (fileName.find(".root") != std::string::npos)
		InitData(fileName);
	else
		InitToyMC(fileName);
	m_dataIsLoaded = true;
	cout << " finished preparation of " << m_name << " data <------ " << endl;  
}
void dybSpectrum::AddGamma(string name,string pdfName,double eTruGam)
{
	std::cout << " adding " << name << " peak" << std::endl;
	dybGammaPeak peak(name.c_str(),pdfName.c_str(),eTruGam,eTruGam);
	s_gammaPeaks.push_back(peak);
}
void dybSpectrum::PrepGaus()
{
	if(s_gausTableReady) return;
	std::cout << " ----> Preparing Gaussian lookup table " << std::endl;
	double dist = 0;
	for (int energyIdx = 0; energyIdx < s_nGausTable; energyIdx++)
	{
		s_gausTable[energyIdx] = TMath::Gaus(dist,5,1,true);
		if(dist>10) s_gausTable[energyIdx] = 0;
		dist += s_gausTableRes;
	}
	s_gausTableReady = true;
}
namespace {

double branchWeightForEntry(const std::string& name,
                            int isotope,
                            int branchIdx,
                            double normalizedBR,
                            double componentScale)
{
	if(name=="B12" && isotope==0){
		if(branchIdx==0) return dybParameters::b12Branch0;
		if(branchIdx==1) return dybParameters::b12Branch1;
		if(branchIdx==2) return dybParameters::b12Branch2;
		return 0.0;
	}
	if(name=="B12" && isotope==1){
		if(branchIdx==0) return dybParameters::n12Branch0;
		if(branchIdx==1) return dybParameters::n12Branch1;
		if(branchIdx==2) return dybParameters::n12Branch2;
		if(branchIdx==3) return dybParameters::n12Branch3;
		if(branchIdx==4) return dybParameters::n12Branch4;
		return 0.0;
	}
	return normalizedBR * componentScale;
}

}  // namespace

void dybSpectrum::TheoHistTree(string filename,int isotope,int branchOffset,double componentScale)
{
	double energyScale = 1.0;
	if(m_name=="Bi212") energyScale = 1.0;
	if(m_name=="Bi214") energyScale = 0.992;
	if(m_name=="Tl208") energyScale = 0.998;
        if(m_name=="K40") energyScale = s_k40Scale;

	TFile *file = new TFile(filename.c_str());
    if(!file || file->IsZombie()){
        cout<<"Reading "<<filename.c_str()<<" FILE NOT FOUND!!!"<<endl;
        delete file;
        gROOT->cd();
        return;
    }
	TTree *tree = (TTree*)file->Get("T");
    if(!tree) {
        cout<<"Reading "<<filename.c_str()<<" Tree T Null???"<<endl;
        delete file;
        gROOT->cd();
        return;
    }
	int nGamma,branchNumber;
	double branchRatio;
	double weight;
	std::vector<double>* photonEV = 0;
	tree->SetBranchAddress("num"      ,&branchNumber);
	tree->SetBranchAddress("BR"       ,&branchRatio);
	tree->SetBranchAddress("numPhoton",&nGamma);
	tree->SetBranchAddress("photonE"  ,&photonEV);

	const Long64_t nEntries = tree->GetEntries();
	double sumBR = 0.0;
	for(Long64_t entryIdx=0; entryIdx<nEntries; ++entryIdx){
		tree->GetEntry(entryIdx);
		sumBR += branchRatio;
	}
	if(sumBR<=0.0) sumBR = 1.0;

	for (Long64_t branchIdx=0; branchIdx<nEntries; ++branchIdx){
		tree->GetEntry(branchIdx);
		const int localIdx = branchOffset + int(branchIdx);
		if(localIdx<0 || localIdx>=int(m_nBr)){
			cout<<"WARNING: branch offset out of range in "<<filename<<endl;
			continue;
		}
		for (int gamIdx=0; gamIdx<m_nGam; ++gamIdx){
			m_eTruGam[localIdx][gamIdx] = 0.0;
		}
		if(photonEV){
			for (int gamIdx=0; gamIdx<nGamma && gamIdx<int(m_nGam); ++gamIdx){
				m_eTruGam[localIdx][gamIdx] = (*photonEV)[gamIdx]/energyScale;
			}
		}
		TH1F* electronHist = (TH1F*)file->Get(Form("hh%d",branchNumber));
		if(!electronHist){
			cout<<"Reading "<<m_name<<" hh"<<branchNumber<<" NOT FOUND in "<<filename<<endl;
			continue;
		}
		const double brWeight = branchWeightForEntry(m_name, isotope, int(branchIdx), branchRatio/sumBR, componentScale);

		for (int binIdx=0;binIdx!=int(m_nBins);binIdx++)
		{
			weight = electronHist->Interpolate(m_binCenter[binIdx]*energyScale);
			if(isotope==0)
                        {
				if(m_name=="K40"&&branchIdx==1&&binIdx==0)
					m_eTru[localIdx][binIdx] = brWeight*energyScale*10.;
				else
					m_eTru[localIdx][binIdx] = brWeight * weight;
                        }
			else
				m_eTruBck[localIdx][binIdx] = brWeight * weight;
		}
	}
	file->Close();
	delete file;
}
void dybSpectrum::DataHist(string fileName)
{
	std::cout << " ----> Reading " << m_name << " data from " << fileName << std::endl;
	TFile* file = new TFile(fileName.c_str());
	TH1F* sigH  = (TH1F*)file->Get("Michel");
	for (int i=0;i!=m_nBinsData;i++)
	{
		double content = sigH->GetBinContent(i+1);
		double error   = sigH->GetBinError  (i+1);
		m_eData   [i] = content;
		m_eDataErr[i] = error;
	}
	//delete sigH;
	file->Close();
	delete file;
}
void dybSpectrum::InitToyMC(string fileName)
{
	std::cout << " ----> Reading B12 toy MC from " << fileName << std::endl;
	ifstream infile(fileName.c_str());
	int i = 0;
	double energy,entries,error;
	while (infile >> energy >> entries >> error)
	{
		m_eData   [i] = entries;
		m_eDataErr[i] = error;
		i++;
	}
	if(i>m_nBinsData) std::cout << " ERROR: B12 toy MC contains more bins than initialized! " << std::endl;
	if(i<m_nBinsData) std::cout << " ERROR: B12 toy MC contains less bins than initialized! " << std::endl;
}
void dybSpectrum::AddBackground()
{
	for (int i = 0; i < m_nBins; i++)
	{
		m_eRecBck[i] *= s_n12Ratio;
		m_eRec[i]    += m_eRecBck[i];
	}
}
void dybSpectrum::Normalize()
{
	int   rebin = m_nBins/m_nBinsData;
	double binWidthData = m_binWidth * rebin;
	double nTheo = 0;
	double nData = 0;
	for (int i = 0; i < m_nBinsData; i++)
	{
		m_eTheo[i] = 0;
		for (int j = 0; j < rebin; j++)
			m_eTheo[i] += m_eRec[i*rebin+j];
		if(i*binWidthData>m_fitMin && i*binWidthData<m_fitMax)
		{
			nTheo += m_eTheo[i];
			nData += m_eData[i];
		}
	}
	double scale = nData/nTheo;
	m_lastNormScale = scale;
	for (int i = 0; i < m_nBinsData; i++)
		m_eTheo[i] *= scale;
	for (int i = 0; i < m_nBins; i++)
	{
		m_eRec   [i] *= scale;
		m_eRecBck[i] *= scale;
	}
}
double dybSpectrum::GetChi2(int nDoF)
{
	InitTheo();
	ApplyScintillatorNL();
	ApplyElectronicsNL ();
	AddBackground      ();
	Normalize          ();
	double chi2 = 0;
	int   rebin = m_nBins/m_nBinsData;
	double binWidthData = m_binWidth * rebin;
	m_nData = 0;
	for (int i = 0; i < m_nBinsData; i++)
	{
		if(i*binWidthData<m_fitMin||i*binWidthData>=m_fitMax-0.1) continue;
		chi2 += pow((m_eData[i]-m_eTheo[i])/m_eDataErr[i],2);
		m_nData++;
		//std::cout << " chi2 = " << chi2 << std::endl;
	}
	if(nDoF>0) chi2 /= double(m_nData - nDoF);
	return chi2;
}
void dybSpectrum::ApplyScintillatorNL()
{

	for(int i=0; i<m_nBins; i++)
	{
		m_eVis   [i] = 0;
		m_eVisBck[i] = 0;
	}
	int    newBin,newBinBck;
	int    newBinLow,newBinLowBck;
	int    newBinHig,newBinHigBck;
	double bias,biasBck;
	double eTru;
	double eVis,eVisBck;
	double eVisElec;
	vector<double> eVisGam;
	double eVisAnn = 2.*GetEVisGamma(0.511);
	//double eVisAnn = 0;
	for(int branchIdx=0; branchIdx<m_nBr; branchIdx++)
	{
		//eVisGam[branchIdx] = 0;
		eVisGam.push_back(0);
		for (int gamIdx = 0; gamIdx < m_nGam; gamIdx++)
		{
			if(m_eTruGam[branchIdx][gamIdx]==0) break;
			eVisGam[branchIdx] += GetEVisGamma(m_eTruGam[branchIdx][gamIdx]);
		}
	}
	for(int i=0; i<m_nBins; i++)
	{
		eTru     = m_binCenter[i];
		eVisElec = eTru * dybEnergyModel::ScintillatorNL(eTru);
		for(int branchIdx=0; branchIdx<m_nBr; branchIdx++)
		{       
                        if(m_name=="K40"&&branchIdx==1&&i>0) continue;
			eVis    = eVisElec + eVisGam[branchIdx];
                        if(m_name=="K40"&&branchIdx==1)  eVis = eVisGam[branchIdx];
			if(m_name=="B12"&&branchIdx==2) eVis += 0.5;  
            if(m_name=="C11" || m_name=="C10") eVis += eVisAnn;
			eVisBck = eVis     + eVisAnn;
			newBinLow    = int((eVis   -m_eMin)/m_binWidth);
			newBinLowBck = int((eVisBck-m_eMin)/m_binWidth);
			newBinHig    = int((eVis   -m_eMin)/m_binWidth)+1;
			newBinHigBck = int((eVisBck-m_eMin)/m_binWidth)+1;
			bias         = (eVis    -m_eMin - newBinLow   *m_binWidth)/m_binWidth;
			biasBck      = (eVisBck -m_eMin - newBinLowBck*m_binWidth)/m_binWidth;
			if(newBinLow<m_nBins)    m_eVis   [newBinLow   ] += (1-bias   )*m_eTru   [branchIdx][i];
			if(newBinLowBck<m_nBins) m_eVisBck[newBinLowBck] += (1-biasBck)*m_eTruBck[branchIdx][i];
			if(newBinHig<m_nBins)    m_eVis   [newBinHig   ] +=    bias    *m_eTru   [branchIdx][i];
			if(newBinHigBck<m_nBins) m_eVisBck[newBinHigBck] +=    biasBck *m_eTruBck[branchIdx][i];
		}
	}
}
void dybSpectrum::ApplyElectronicsNL()
{
	for(int i=0; i<m_nBins; i++)
	{
		m_eRec   [i] = 0;
		m_eRecBck[i] = 0;
	}
	int    newBin;
	int    sigmaIdx;
	int    distIdx;
	double eVis;
	double eRec;
	double energy;
	double sigma,sigmaInv;
	double weight;
	double dist;
	int minBin,maxBin;
	double binCon,binConBck;
	int minBinGen = 0;
	int maxBinGen = m_nBins-1;
	if(m_opt)
	{
		minBinGen = m_fitMinBin-m_nBins/m_nBinsData;
		maxBinGen = m_fitMaxBin+m_nBins/m_nBinsData;
	}
	double resid;
	for(int i=0; i<m_nBins; i++)
	{
		eVis      = m_binCenter[i];
		eRec      = eVis * dybEnergyModel::ElectronicsNL (eVis);
		sigma     = dybEnergyModel::Resolution(eRec);
                if(m_name=="K40")  sigma     = dybEnergyModel::Resolution_K40(eRec);
		sigmaInv  = 1/sigma;
		minBin    = int((eRec-m_eMin-4.5*sigma)/m_binWidth);
		maxBin    = int((eRec-m_eMin+4.5*sigma)/m_binWidth);
		if(minBin<minBinGen) minBin=minBinGen;
		if(maxBin>maxBinGen) maxBin=maxBinGen;
		
		binCon    = m_eVis   [i]*m_binWidth;
		binConBck = m_eVisBck[i]*m_binWidth;
		for(int j=minBin; j<maxBin; j++)
		{
			energy = m_binCenter[j];
			
			dist    = (energy-eRec)*sigmaInv + 5;
			if(dist<0) continue;
			distIdx = int(dist*s_gausTableResR);
			resid = dist*s_gausTableResR - distIdx;
			weight = ((1-resid)*s_gausTable[distIdx]
									+resid *s_gausTable[distIdx+1])*sigmaInv;
			m_eRec   [j] += weight*binCon;
			m_eRecBck[j] += weight*binConBck;
			
		}
	}
}
void dybSpectrum::FillComponentRec(double* eRecOut, int brFirst, int brLast)
{
	if(brFirst < 0) brFirst = 0;
	if(brLast >= int(m_nBr)) brLast = int(m_nBr) - 1;
	if(brFirst > brLast) return;

	for(int i = 0; i < int(m_nBins); i++)
		eRecOut[i] = 0.0;

	double* eVisComp = new double[m_nBins];
	for(int i = 0; i < int(m_nBins); i++)
		eVisComp[i] = 0.0;

	vector<double> eVisGam;
	double eVisAnn = 2. * GetEVisGamma(0.511);
	for(int branchIdx = brFirst; branchIdx <= brLast; branchIdx++)
	{
		double gamSum = 0.0;
		for(int gamIdx = 0; gamIdx < int(m_nGam); gamIdx++)
		{
			if(m_eTruGam[branchIdx][gamIdx] == 0) break;
			gamSum += GetEVisGamma(m_eTruGam[branchIdx][gamIdx]);
		}
		eVisGam.push_back(gamSum);
	}

	for(int i = 0; i < int(m_nBins); i++)
	{
		double eTru     = m_binCenter[i];
		double eVisElec = eTru * dybEnergyModel::ScintillatorNL(eTru);
		for(int br = brFirst; br <= brLast; br++)
		{
			int gamIdx = br - brFirst;
			double eVis = eVisElec + eVisGam[gamIdx];
			if(m_name == "B12" && br == 2) eVis += 0.5;
			if(m_name == "C11" || m_name == "C10") eVis += eVisAnn;

			int newBinLow = int((eVis - m_eMin) / m_binWidth);
			int newBinHig = newBinLow + 1;
			double bias   = (eVis - m_eMin - newBinLow * m_binWidth) / m_binWidth;
			if(newBinLow < int(m_nBins))
				eVisComp[newBinLow] += (1.0 - bias) * m_eTru[br][i];
			if(newBinHig < int(m_nBins))
				eVisComp[newBinHig] += bias * m_eTru[br][i];
		}
	}

	int minBinGen = 0;
	int maxBinGen = int(m_nBins) - 1;
	double resid;
	for(int i = 0; i < int(m_nBins); i++)
	{
		double eVis = m_binCenter[i];
		double eRec = eVis * dybEnergyModel::ElectronicsNL(eVis);
		double sigma = dybEnergyModel::Resolution(eRec);
		if(m_name == "K40") sigma = dybEnergyModel::Resolution_K40(eRec);
		double sigmaInv = 1.0 / sigma;
		int minBin = int((eRec - m_eMin - 4.5 * sigma) / m_binWidth);
		int maxBin = int((eRec - m_eMin + 4.5 * sigma) / m_binWidth);
		if(minBin < minBinGen) minBin = minBinGen;
		if(maxBin > maxBinGen) maxBin = maxBinGen;

		double binCon = eVisComp[i] * m_binWidth;
		for(int j = minBin; j <= maxBin; j++)
		{
			double energy = m_binCenter[j];
			double dist   = (energy - eRec) * sigmaInv + 5.0;
			if(dist < 0) continue;
			int distIdx = int(dist * s_gausTableResR);
			resid = dist * s_gausTableResR - distIdx;
			double weight = ((1.0 - resid) * s_gausTable[distIdx]
			                 + resid * s_gausTable[distIdx + 1]) * sigmaInv;
			eRecOut[j] += weight * binCon;
		}
	}
	delete [] eVisComp;
}
double dybSpectrum::GetEVisGamma(double eTruGam)
{
	if(eTruGam<0.2) return 0;
	//double nlGam1 = 1;
	//std::cout << " ----> checking for E = " << eTruGam << std::endl;
	int nGamma = s_gammaPeaks.size();
	for (int gamIdx=0; gamIdx<nGamma; gamIdx++)
	{
		double energyHigh = s_gammaPeaks[gamIdx].GetETruSingle();
		//std::cout << " smaple = " << energyHigh << std::endl;
		if(energyHigh > eTruGam)
		{
			s_gammaPeaks[gamIdx]  .UpdateTheoNL();
			s_gammaPeaks[gamIdx-1].UpdateTheoNL();
			double nlHigh = s_gammaPeaks[gamIdx]  .GetTheoScintNL();
			double nlLow  = s_gammaPeaks[gamIdx-1].GetTheoScintNL();
			double energyLow = s_gammaPeaks[gamIdx-1].GetETruSingle();
			double resid = (eTruGam-energyLow)/(energyHigh-energyLow);
			double nlGam = resid*nlHigh + (1-resid)*nlLow;
			return nlGam*eTruGam;
		}
	}
}
TH1F dybSpectrum::PlotSpec(int type)
{
	m_opt = false;
	double chi2 = GetChi2();
	m_opt = true;
	int nBins = m_nBins;
	if(type==0 || type==10) nBins = m_nBinsData;
	TH1F hist("hist","",nBins,m_eMin,m_eMax);
	hist.SetLineColor(kRed+2);
	if(type==10) hist.SetLineColor(kBlue+1);
	double error;
	for(int i=0; i<nBins; i++)
	{
		double entries = 0;
		if(type==0){entries = m_eData  [i]; error = m_eDataErr[i];}
		//if(type==1) entries = m_eTru   [i];
		//if(type==2) entries = m_eVisSig[i];
		if(type==3) entries = m_eRec   [i];
		if(type==5) entries = m_eRecBck[i];
		//if(type==6) entries = m_eRecSig[i];
		if(type==10)entries = m_eTheo  [i];
		hist.SetBinContent(i+1,entries);
		if(type==0) hist.SetBinError(i+1,error);
	}
	//int rebin = nBins/m_nBinsData;
	double scale = float(m_nBinsData)/float(nBins);
	//hist.Rebin(rebin);
	hist.Scale(1/scale);
	return hist;
}
TH1F dybSpectrum::Plot(bool writeToFile)
{
	m_opt = false;
	double chi2 = GetChi2();
	int nFitBins = (m_fitMax-m_fitMin)/(m_eMax-m_eMin) * m_nBinsData;
	stringstream ssChi2;ssChi2.precision(3);ssChi2<<chi2;
	stringstream ssBins;ssBins<<nFitBins;
	m_opt = true;
	TH1F dataH ("dataH", "",m_nBinsData,m_eMin,m_eMax);
	TH1F theoH ("theoH", "",m_nBinsData,m_eMin,m_eMax);
	TH1F eRecH ("eRecH", "",m_nBins    ,m_eMin,m_eMax);
	TH1F b12H  ("b12H" , "",m_nBins    ,m_eMin,m_eMax);
	TH1F n12H  ("n12H" , "",m_nBins    ,m_eMin,m_eMax);
	TH1F c10H  ("c10H" , "",m_nBins    ,m_eMin,m_eMax);
	TH1F c11H  ("c11H" , "",m_nBins    ,m_eMin,m_eMax);
	TH1F be11H ("be11H", "",m_nBins    ,m_eMin,m_eMax);
	TH1F ratioH("ratioH","",m_nBinsData,m_eMin,m_eMax);
	const bool isC10 = (m_name == "C10");
	const bool isC11 = (m_name == "C11");
    const int font = 133; //133
	dataH.GetXaxis()->SetTitleFont(font);
	dataH.GetYaxis()->SetTitleFont(font);
	dataH.GetXaxis()->SetLabelFont(font);
	dataH.GetYaxis()->SetLabelFont(font);
	dataH.GetXaxis()->SetTitleSize(21);
	dataH.GetYaxis()->SetTitleSize(21);
	dataH.GetXaxis()->SetLabelSize(19);
	dataH.GetYaxis()->SetLabelSize(17);
	
	dataH.SetStats(0);
	dataH.SetMarkerStyle(20);
	dataH.SetMarkerSize (0.8);
	ratioH.SetStats(0);
	ratioH.SetMarkerStyle(20);
	ratioH.SetMarkerSize (0.8);
	dataH.SetMarkerColor (kBlue+1);
	dataH.SetLineColor   (kBlue+1);
	ratioH.SetMarkerColor(kBlue+1);
	ratioH.SetLineColor  (kBlue+1);
	eRecH.SetLineColor  (kRed+1);
	eRecH.SetFillColor  (19);
	theoH.SetLineColor  (kRed+1);
	theoH.SetFillColor  (19);
	theoH.SetLineWidth  (2);
	b12H.SetLineColor   (kBlue+2);
	n12H.SetLineColor   (kRed+3);
	eRecH.SetLineWidth  (2);
	b12H.SetLineWidth   (2);
	n12H.SetLineWidth   (3);
	b12H.SetLineStyle   (2);
	n12H.SetLineStyle   (3);
	c10H.SetLineColor   (kBlue+2);
	c11H.SetLineColor   (kRed+3);
	be11H.SetLineColor  (kGreen+2);
	c10H.SetLineWidth   (2);
	c11H.SetLineWidth   (3);
	be11H.SetLineWidth  (3);
	c10H.SetLineStyle   (2);
	c11H.SetLineStyle   (3);
	be11H.SetLineStyle  (4);
	int count = 0 ;
	for(int i=0; i<m_nBins; i++)
	{
		if(m_eMin>0)std::cout << i << ": " << m_eTru[0][i] << std::endl;
		
		eRecH.SetBinContent(i+1,m_eRec    [i]);
		b12H .SetBinContent(i+1,m_eRec    [i]);
		n12H .SetBinContent(i+1,m_eRecBck [i]);
		if(i>=m_nBinsData) continue;
		
		theoH.SetBinContent(i+1,m_eTheo   [i]);
		double energy = dataH.GetBinCenter(i+1);
		//if(energy<3.8) continue;
		//if(energy<m_fitMin-0.1) continue;
		//cout<<i<<" "<<m_eDataErr[i]<<endl;
		//if(energy<m_fitMin) continue;
		if(energy>m_fitMax) continue;
		dataH.SetBinContent(i+1,m_eData   [i]);
		dataH.SetBinError  (i+1,m_eDataErr[i]);
		if(energy<m_fitMin) continue;
		double ratio  = m_eData   [i]/m_eTheo[i];
		//ratio = 1;
		double ratioE = m_eDataErr[i]/m_eData[i];
		ratioH.SetBinContent(i+1,ratio);
		ratioH.SetBinError  (i+1,ratioE);
	}
	b12H.Add(&n12H,-1);
	if(isC10)
	{
		double* compRec = new double[m_nBins];
		FillComponentRec(compRec, 0, 1);
		for(int i = 0; i < int(m_nBins); i++)
			c10H.SetBinContent(i + 1, compRec[i] * m_lastNormScale);
		FillComponentRec(compRec, 2, 2);
		for(int i = 0; i < int(m_nBins); i++)
			c11H.SetBinContent(i + 1, compRec[i] * m_lastNormScale);
		FillComponentRec(compRec, 3, int(m_nBr) - 1);
		for(int i = 0; i < int(m_nBins); i++)
			be11H.SetBinContent(i + 1, compRec[i] * m_lastNormScale);
		delete [] compRec;
	}
	double scale = float(m_nBinsData)/float(m_nBins);
	eRecH.Scale(1/scale);
	b12H. Scale(1/scale);
	n12H. Scale(1/scale);
	if(m_name.find("B12")!= std::string::npos) {
		b12H.Rebin(40);
		n12H.Rebin(40);
		b12H.Scale(0.025);
		n12H.Scale(0.025);
	}
	if(isC10) {
		c10H.Scale(1/scale);
		c11H.Scale(1/scale);
		be11H.Scale(1/scale);
		c10H.Rebin(40);
		c11H.Rebin(40);
		be11H.Rebin(40);
		c10H.Scale(0.025);
		c11H.Scale(0.025);
		be11H.Scale(0.025);
	}
	
	TCanvas* tmpC = new TCanvas("tmpH","",700,520);
	
	TString name = dybParameters::title;
	
	double binWidthData = m_eMax / m_nBinsData;
	stringstream ssBinWidth;ssBinWidth.precision(2);ssBinWidth<<binWidthData;
	//TString specTitle = m_title+" decay spectrum: #chi^{2} = "+ssChi2.str()+" / "+ssBins.str()+" bins;Reconstructed Energy [MeV];Events / " +ssBinWidth.str() + " MeV";
	TString specTitle = " ;Reconstructed Energy [MeV];Events / " +ssBinWidth.str() + " MeV";
	
	//if(m_name.find("Bi214")!= std::string::npos)
		//specTitle = "^{214}Bi #rightarrow ^{214}Po + #beta^{-} (Q=3.27 MeV);Prompt energy [MeV];Events / " +ssBinWidth.str() + " MeV";
	//if(m_name.find("Bi212")!= std::string::npos)
		//specTitle = "^{212}Bi #rightarrow ^{212}Po + #beta^{-} (Q=2.25 MeV);Prompt energy [MeV];Events / " +ssBinWidth.str() + " MeV";
	//if(m_name.find("Tl208")!= std::string::npos)
		//specTitle = "^{208}Tl #rightarrow ^{208}Pb + #beta^{-} (Q=4.99 MeV);Energy [MeV];Events / " +ssBinWidth.str() + " MeV";
	//if(m_name.find("B12")!= std::string::npos)
		//specTitle = "^{12}B #rightarrow ^{12}C + #beta^{-} (Q=13.37 MeV);Energy [MeV];Events / " +ssBinWidth.str() + " MeV";

	//TString specTitle = "Raw ^{12}B spectrum;Reconstructed Energy [MeV]";
	
	//dataH.GetYaxis()->SetRangeUser(0,3500);
	//dataH.GetYaxis()->SetLimits(0,3500);
	//if(m_name.find("Tl208")!= std::string::npos)
	//{
		//dataH.GetXaxis()->SetRangeUser(3,5);
		//dataH.GetYaxis()->SetRangeUser(0,3500);
	//}
	//if(m_name.find("Bi214")!= std::string::npos)
	//{
		//dataH.GetXaxis()->SetRangeUser(1,3);
		//dataH.GetYaxis()->SetRangeUser(0,3500);
	//}
	
	gStyle->SetTitleSize(0.05,"T"); 
	dataH.SetTitle(specTitle);
	dataH.SetMinimum(0);
	dataH.Draw("PEX0");
	//theoH.Draw("hist same");
	theoH.Draw("C hist same");
	if(m_name.find("B12")!= std::string::npos)
	{
		b12H .Draw("C same");
		n12H .Draw("C same");
	}
	if(isC10)
	{
		c10H .Draw("C same");
		c11H .Draw("C same");
		be11H.Draw("C same");
	}
	dataH.Draw("sameaxis");
	dataH.Draw("PEX0 same");
	//dataH.Draw("sameaxis");
	TLegend* leg =new TLegend(0.7,0.85,0.89,0.92);
	TLegend* legP=new TLegend(0.7,0.62,0.89,0.845);
	//TLegend* leg =new TLegend(0.73,0.85,0.92,0.92);
	//TLegend* legP=new TLegend(0.73,0.62,0.92,0.845);
	leg->SetFillColor(-1);
	leg->SetTextFont(font);
	TLegendEntry *le = leg->AddEntry((TObject*)0,"JUNO Data","PE");
	//leg->AddEntry(&b12H," "," ");
	le->SetMarkerStyle(20); 
	le->SetMarkerSize(1.0); 
	le->SetMarkerColor(kBlue+1); 
	le->SetLineColor  (kBlue+1); 
	leg->SetTextSize(19);
	//if(m_eMax>10) leg->Draw();
	stringstream ssN12;ssN12.precision(2);ssN12<<s_n12Ratio*100;
	TString n12Str = ssN12.str();
	stringstream ssC11;ssC11.precision(2);ssC11<<s_c10C11Frac*100;
	TString c11Str = ssC11.str();
	stringstream ssBe11;ssBe11.precision(2);ssBe11<<s_c10Be11Frac*100;
	TString be11Str = ssBe11.str();
	
	legP->SetFillColor(-1);
    legP->SetTextFont(font);
	if(m_name.find("B12")!= std::string::npos)  {
		legP->SetHeader("Best fit model");
		//legP->SetHeader("Prediction");
		legP->AddEntry(&theoH,"Total","F");
		//legP->AddEntry(&theoH,"Total","L");
		legP->AddEntry(&b12H,"^{12}B","L");
		legP->AddEntry(&n12H,"^{12}N: "+ n12Str + "%","L");
		//legP->AddEntry(&n12H,"^{12}N","L");
	}
	else if(isC10) {
		legP->SetHeader("Best fit model");
		legP->AddEntry(&theoH,"Total","F");
		legP->AddEntry(&c10H,"^{10}C","L");
		legP->AddEntry(&c11H,"^{11}C: "+ c11Str + "%","L");
		legP->AddEntry(&be11H,"^{11}Be: "+ be11Str + "%","L");
	}
	else  {
		legP->AddEntry(&theoH,"Best fit","F");
		//legP->AddEntry(&theoH,"Analytical prediction","F");
		legP->AddEntry(&theoH," "," ");
		legP->AddEntry(&theoH," "," ");
		legP->AddEntry(&theoH," "," ");
	}
	legP->SetFillStyle(0);
	legP->SetTextSize(19);
	leg ->Draw();
	//legP->Draw();
	string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_"+m_name+"_log0."+dybParameters::plotFormat;
	tmpC->SetLogy();
	if(m_name.find("B12")!= std::string::npos) 
		tmpC->SaveAs(plotName.c_str());
	delete tmpC;
	
	dataH.SetTitle(specTitle);
	dataH.SetMinimum(0);
	double xDrawMin = m_eMinDraw;
	double xDrawMax = (m_eMaxDraw > 0.0) ? m_eMaxDraw : m_eMax;
	dataH.GetXaxis()->SetRangeUser(xDrawMin, xDrawMax);
	ratioH.GetXaxis()->SetRangeUser(xDrawMin, xDrawMax);
	ratioH.GetYaxis()->SetNdivisions(505);
	ratioH.SetMinimum(0.93);
	ratioH.SetMaximum(1.07);
        if(m_name.find("K40")!= std::string::npos)
          {
          ratioH.SetMinimum(0.7);
          ratioH.SetMaximum(1.3);
          }
	ratioH.GetXaxis()->SetLabelSize(19);  
	ratioH.GetYaxis()->SetLabelSize(19);  
	ratioH.GetXaxis()->SetTitleSize(21);  
	ratioH.GetXaxis()->SetTitle("Reconstructed Energy [MeV]"); 
	
	TCanvas* tmpC2 = new TCanvas("tmpC","",700,520);
	
	TPad *pad1 = new TPad("pad1","pad1",0,0.3,1,1);
	pad1->SetBottomMargin(0);
	pad1->Draw();
	TPad *pad2 = new TPad("pad2","pad2",0,0,1,0.3);
	pad2->SetTopMargin(0);
	pad2->SetBottomMargin(0.35);
	pad2->SetGridy();
	pad2->Draw();
	pad1->cd();
	
	float oldSize = gStyle->GetTitleSize("T");
	gStyle->SetTitleSize(0.06,"T");  
	//gStyle->SetTitleFont(font,"T");  
	//gStyle->SetLabelFont(font,"XY");  
	//gStyle->SetTitleSize(21,"T");  
	
	if(b12H.GetMaximum()>dataH.GetMaximum())
		dataH.SetMaximum(b12H.GetMaximum()*1.05);
	if(isC10)
	{
		double compMax = c10H.GetMaximum();
		if(c11H.GetMaximum() > compMax) compMax = c11H.GetMaximum();
		if(be11H.GetMaximum() > compMax) compMax = be11H.GetMaximum();
		if(compMax > dataH.GetMaximum())
			dataH.SetMaximum(compMax * 1.05);
	}
	//dataH.SetMarkerSize(0);  
	//theoH.SetLineColor(kBlue+2);  
	//dataH.GetXaxis()->SetRangeUser(0,16);
	//dataH.DrawCopy("PX");
	dataH.SetMinimum(1);
	dataH.GetYaxis()->SetTitleOffset(1.15);
	dataH.GetXaxis()->SetTickLength (0.05);
	if(isC10 || isC11)
		pad1->SetLogy(1);
	else
		pad1->SetLogy(0);
	dataH.DrawCopy("PEX0");
	theoH.DrawCopy("C hist same");
	if(m_name.find("B12")!= std::string::npos)	{
		b12H .Draw("C same");
		n12H .Draw("C same");
	}
	if(isC10) {
		c10H .Draw("C same");
		c11H .Draw("C same");
		be11H.Draw("C same");
	}
	
	
	dataH.DrawCopy("sameaxis");
	dataH.DrawCopy("PEX0 same");
	
	pad2->cd();
	ratioH.GetYaxis()->SetTitleOffset(1.15);
	ratioH.GetXaxis()->SetTickLength (0.1);  
	ratioH.GetXaxis()->SetTitleOffset(3.0);  
	ratioH.GetXaxis()->SetTitleFont(font);  
	ratioH.GetXaxis()->SetLabelFont(font);  
	ratioH.GetYaxis()->SetTitleFont(font);  
	ratioH.GetYaxis()->SetLabelFont(font);  
	ratioH.GetXaxis()->SetTitleSize(21);  
	ratioH.GetXaxis()->SetLabelSize(19);  
	ratioH.GetYaxis()->SetTitleSize(21);  
	ratioH.GetYaxis()->SetLabelSize(18);  
	ratioH.GetXaxis()->SetTickLength (0.05); 
	ratioH.SetTitle(";Reconstructed energy [MeV];Data / best fit");
	ratioH.Draw("PEX0");
	TF1 oneF("lineF","pol0",xDrawMin,xDrawMax);
	oneF.SetLineWidth(1);
	oneF.SetParameter(0,1); 
	oneF.SetLineWidth(2);
	oneF.SetLineColor(kRed+1);
	oneF.Draw("same");
	ratioH.Draw("PE0X0 same");
	tmpC2->cd();
	leg->Draw();
	legP->Draw();
	plotName = dybParameters::plotFolder+dybParameters::toyKey+"_"+m_name+"."+dybParameters::plotFormat;
	tmpC2->SaveAs(plotName.c_str());
    plotName = dybParameters::plotFolder+"../Hist_"+m_name+"_"+dybParameters::toyKey+".root";
    TFile* fout = new TFile(plotName.c_str(),"RECREATE");
    dataH.Write("data");
    theoH.Write("theo");
    b12H.Write("b12");
    n12H.Write("n12");
    if(isC10) {
        c10H.Write("c10");
        c11H.Write("c11");
        be11H.Write("be11");
    }
    ratioH.Write("ratio");
    oneF.Write("line");
    fout->Close();	
	
	if(m_name.find("B12")!= std::string::npos)	
	{
		dataH.SetMinimum(3);
		pad1->SetLogy();
		plotName = dybParameters::plotFolder+dybParameters::toyKey+"_"+m_name+"_log."+dybParameters::plotFormat;
		tmpC2->SaveAs(plotName.c_str());
		delete tmpC2;
	}
	gStyle->SetTitleSize(oldSize,"T");  
	if(writeToFile)
	{
		TFile* b12File = new TFile("ibdFile.root","recreate");
		dataH.Write();
		theoH.Write();
		ratioH.Write();
		b12File->Close();
		delete b12File;
	}
	return dataH;
}
void dybSpectrum::GenToyMC()
{
	std::cout << " ------> Generating " << dybParameters::nToy << " B12 toy MC samples " << std::endl;
	ApplyScintillatorNL();
	ApplyElectronicsNL ();
	AddBackground      ();
	Normalize          ();
	TRandom3 rand;
	for (int toyIdx=0; toyIdx<dybParameters::nToy; toyIdx++)
	{
		stringstream ss; ss<<toyIdx;
		std::string toyName = dybParameters::toyFolder;
                toyName += "k40Toy_" + dybParameters::toyKey + "_" +  ss.str() + ".root";
		TH1F hist("k40","k40",m_nBinsData,0,2);
		for (int i=0; i<m_nBinsData; i++)
		{
			double energy  = m_binCenter[i];
			double error   = m_eDataErr [i]; 
			double entries = int(rand.Gaus(m_eTheo[i],error)+0.5);
			if(entries<0 || error==0) entries = 0;
			hist.SetBinContent(i,entries);
			hist.SetBinError(i,error);
		}
		TFile nf1(toyName.c_str(),"recreate");
                hist.Write();
	}
}

double dybSpectrum::WMCorrection(string name_WM,int branchIdx_WM,double T)
{
        if(name_WM=="B12"&&branchIdx_WM==0)
                return 1 - (1 - 0.00184367*T - 0.988041)*(s_b12branch0WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="B12"&&branchIdx_WM==1)
                return 1 - (1 - 0.0018927*T - 0.991955)*(s_b12branch1WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="B12"&&branchIdx_WM==2)
                return 1 - (1 - 0.00192603*T - 0.994906)*(s_b12branch2WM - dybParameters::universalWM)/dybParameters::WMError;

        if(name_WM=="N12"&&branchIdx_WM==0)
                return 1 - (1 + 0.00221296*T - 1.01735)*(s_n12branch0WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="N12"&&branchIdx_WM==1)
                return 1 - (1 + 0.00215965*T - 1.01223)*(s_n12branch1WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="N12"&&branchIdx_WM==2)
                return 1 - (1 + 0.0021131*T - 1.00863)*(s_n12branch2WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="N12"&&branchIdx_WM==3)
                return 1 - (1 + 0.00208382*T - 1.0058)*(s_n12branch3WM - dybParameters::universalWM)/dybParameters::WMError;
        if(name_WM=="N12"&&branchIdx_WM==4)
                return 1 - (1 + 0.00205206*T - 1.00331)*(s_n12branch4WM - dybParameters::universalWM)/dybParameters::WMError;
}

// Initialize static constant members
const double dybSpectrum::s_gausTableRes = 0.0001;
const double dybSpectrum::s_gausTableResR = 10000;
