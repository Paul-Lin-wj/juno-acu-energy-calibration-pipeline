#include "dybEnergyModel.h"

std::string dybEnergyModel::s_key = "arb";

double dybEnergyModel::s_p0   = 1.;
double dybEnergyModel::s_p1   = 1.;
double dybEnergyModel::s_p2   = 1.;
double dybEnergyModel::s_p3   = 0.;
                              
double dybEnergyModel::s_kB      = 1.;
double dybEnergyModel::s_kB_alpha= 1.;
double dybEnergyModel::s_cer     = 0.;
double dybEnergyModel::s_rad     = 0.;

double dybEnergyModel::s_tau1 = 1.;
double dybEnergyModel::s_tau2 = 1.;
double dybEnergyModel::s_alp1 = 0.1;
double dybEnergyModel::s_alp2 = 0.1;

bool   dybEnergyModel::s_isLoaded = false;
int    dybEnergyModel::s_kBIdx    = 0;
double dybEnergyModel::s_kBResid  = 0;
double dybEnergyModel::s_kBResid_alpha  = 0;

double dybEnergyModel::s_normEnergy  = 0.7;
//double dybEnergyModel::s_normEnergy  = 2.2233;

double dybEnergyModel::s_energySamples         [s_nSamples] = {0};
double dybEnergyModel::s_cerenkovShape         [s_nSamples] = {0};
double dybEnergyModel::s_quenchingShape1[s_nKb][s_nSamples] = {0};
double dybEnergyModel::s_quenchingShape2[s_nKb][s_nSamples] = {0};
double dybEnergyModel::s_quenchingShapeA[s_nKb][s_nSamples] = {0};

double* dybEnergyModel::s_quenchingShape1_lowKb = &s_quenchingShape1[0][0];
double* dybEnergyModel::s_quenchingShape1_higKb = &s_quenchingShape1[0][0];
double* dybEnergyModel::s_quenchingShape2_lowKb = &s_quenchingShape2[0][0];
double* dybEnergyModel::s_quenchingShape2_higKb = &s_quenchingShape2[0][0];
double* dybEnergyModel::s_quenchingShapeA_lowKb = &s_quenchingShapeA[0][0];
double* dybEnergyModel::s_quenchingShapeA_higKb = &s_quenchingShapeA[0][0];

vector<double> dybEnergyModel::m_energySamples;
vector<double> dybEnergyModel::m_grummel;

dybEnergyModel::dybEnergyModel()
{
}
double dybEnergyModel::Resolution(double eVis){
/*
	/// **** P25B: from source data ****
	double b = 0.033427391809514755;
	double a = 0.012264551884720274;
	double c = 0.00000328699616457059;
	/// **** P25C: from source data ****
	double b = 0.03309584607586899;
	double a = 0.012800782361086107;
	double c = 0.000014034481351347132;
*/

	/// **** 26B-PhaseAll: from source data ****
	double b = 0.0326207641;
	double a = 0.0102188403;
	double c = 0.00;
/*
	/// **** 26B-Phase1: from source data ****
	double b = 0.0330808160;
	double a = 0.0085157283;
	double c = 0.0000299882;
	/// **** 26B-Phase2: from source data ****
	double b = 0.0312631214;
	double a = 0.0119474490;
	double c = 0.0085621000;
	/// **** 26B-Phase3: from source data ****
	double b = 0.0323409867;
	double a = 0.0104631592;
	double c = 0.0062155282;
	/// **** 26B-Phase4: from source data ****
	double b = 0.0336644699;
	double a = 0.0084810447;
	double c = 0.0000425302;
*/
	return eVis*sqrt(a*a + b*b/eVis + c*c/(eVis*eVis));
 
}
double dybEnergyModel::Resolution_K40(double eVis){
	double a = 0.016;
        double b = 0.079;
        double c = 0.026;
	return eVis*sqrt(a*a + b*b/eVis + c*c/(eVis*eVis));
}
void dybEnergyModel::Load(){
	std::cout << " ----> Loading quenching+cherenkov shapes " << std::endl;
	if(dybParameters::scintillatorParametrization != kPhysics) {
		s_isLoaded = true; 
		return;
	}
	/// load quenching shapes
	TFile* quenchingFile = new TFile("necessaryfiles/input/Quenching.root","read");
	if (!quenchingFile || quenchingFile->IsZombie()) {
		std::cerr << "ERROR: cannot open necessaryfiles/input/Quenching.root" << std::endl;
		exit(1);
	}
	//for (int kbIdx=20; kbIdx<s_nKb; kbIdx++)  {
	for (int kbIdx=40; kbIdx<s_nKb; kbIdx++)  {
		if(kbIdx%10==0)
		    std::cout << " kB = " << kbIdx/10 << std::endl;
		stringstream ss;ss<<kbIdx*1000;
		TString name1 = "collOnly_kB"+ss.str();
		TString name2 = "collRad_kB" +ss.str();
		TString nameA =   "alpha_kB" +ss.str();
		//TString name1 = "quenNL_kB"+ss.str();
                //TString name2 = "quenNL_kB"+ss.str();
                //TString nameA = "quenNL_kB"+ss.str();

		TGraph* quench1G = (TGraph*)quenchingFile->Get(name1);
		TGraph* quench2G = (TGraph*)quenchingFile->Get(name2);
		TGraph* quenchAG = (TGraph*)quenchingFile->Get(nameA);
		if (!quench1G || !quench2G || !quenchAG) {
			std::cerr << "ERROR: missing quenching graph in Quenching.root: "
			          << name1 << ", " << name2 << ", " << nameA << std::endl;
			exit(1);
		}
		double* quench1 = quench1G->GetY();
		double* quench2 = quench2G->GetY();
		double* quenchA = quenchAG->GetY();
		for (int sampleIdx=0; sampleIdx<s_nSamples; sampleIdx++)
		{      
			s_quenchingShape1[kbIdx][sampleIdx] = quench1[sampleIdx];
			s_quenchingShape2[kbIdx][sampleIdx] = quench2[sampleIdx];
			s_quenchingShapeA[kbIdx][sampleIdx] = quenchA[sampleIdx];
		}
		delete quench1G;
		delete quench2G;
		delete quenchAG;
	}
	quenchingFile->Close();
	delete quenchingFile;
	
	/// load Cerenkov shapes
	ifstream infileC("necessaryfiles/input/cerenkovCurve_2018.dat");
	TGraph cerenkovG(0);
	double xC,yC;
        //std::cout<<"cerenkov curve!!!"<<std::endl;
	for (Int_t i=0;i!=1000;i++){
		infileC >> xC >> yC;
                //std::cout<<xC<<" "<<yC<<std::endl;
		yC = yC/100.;
		cerenkovG.SetPoint(i,xC,yC);
	}
	infileC.close();
	for (int sampleIdx=0; sampleIdx<s_nSamples; sampleIdx++)	{
		double energy = s_samplingResol * sampleIdx;
		s_cerenkovShape[sampleIdx] = cerenkovG.Eval(energy);
	}
	s_isLoaded = true;
}
void dybEnergyModel::Update(){
	if(dybParameters::scintillatorParametrization != kPhysics) return;
	if(!s_isLoaded) Load();
	if(s_kB==0) return;
	int kBIdx = int(s_kB*10);
	if(kBIdx < 0) kBIdx = 0;
	if(kBIdx >= int(s_nKb)-1) kBIdx = int(s_nKb)-2;
	s_kBResid = kBIdx+1 - s_kB*10;
	//cout<<"s_kb "<<s_kB<<' '<<kBIdx<<' '<<s_kBResid<<endl;
	s_quenchingShape1_lowKb = &s_quenchingShape1[kBIdx]  [0];
	s_quenchingShape1_higKb = &s_quenchingShape1[kBIdx+1][0];
	s_quenchingShape2_lowKb = &s_quenchingShape2[kBIdx]  [0];
	s_quenchingShape2_higKb = &s_quenchingShape2[kBIdx+1][0];
	
	int kBIdx_alpha = int(s_kB_alpha*10);
	if(kBIdx_alpha < 0) kBIdx_alpha = 0;
	if(kBIdx_alpha >= int(s_nKb)-1) kBIdx_alpha = int(s_nKb)-2;
	s_kBResid_alpha = kBIdx_alpha+1 - s_kB_alpha*10;
	s_quenchingShapeA_lowKb = &s_quenchingShapeA[kBIdx_alpha]  [0];
	s_quenchingShapeA_higKb = &s_quenchingShapeA[kBIdx_alpha+1][0];
}
double dybEnergyModel::ScintillatorNL(double eTru){
	double norm = 1;
	if(s_normEnergy>0)
		norm = ScintillatorShape(s_normEnergy);
	double nl   = ScintillatorShape(eTru);
	return nl/norm * s_p0;
	//return nl/norm;
        //return nl;
}
double dybEnergyModel::AlphaNL(double eTru){
	if(dybParameters::scintillatorParametrization != kPhysics) return 1.;
	double norm = 1;
	if(s_normEnergy>0)
		norm = ScintillatorShape(s_normEnergy);
	double nl   = AlphaShape(eTru);
	return nl/norm * s_p0;
	//return nl;
}
double dybEnergyModel::ScintillatorShape(double eTru){
	if(!s_isLoaded) Load();
	if(dybParameters::scintillatorParametrization == kSimpleEmpirical)
		return SimpleEmpScintillator(eTru);
	else if(dybParameters::scintillatorParametrization == kLowECorrEmpirical)
		return LowECorrEmpScintillator(eTru);
	else if(dybParameters::scintillatorParametrization == kPhysics)
		//return PhysicsScintillator(eTru)/PhysicsScintillator(dybParameters::anchorEnergy);
		return PhysicsScintillator(eTru);
	else 
		return 1.;
	}
double dybEnergyModel::AlphaShape(double eTru){
	if(!s_isLoaded) Load();
	int idx = int(eTru/s_samplingResol+0.5);
	
	double alphaQuenchNL  =    s_kBResid_alpha *s_quenchingShapeA_lowKb[idx] 
					       +(1-s_kBResid_alpha)*s_quenchingShapeA_higKb[idx];
	return alphaQuenchNL;
}
double dybEnergyModel::ElectronicsNL(double eVis){
  double rescale = 1;
  double nonlin  = 1;
  if(dybParameters::electronicsParametrization == kPolynomial){
    nonlin  = 1 - PolynomialElectronics(dybParameters::anchorEnergy)
                + PolynomialElectronics(eVis);
  }
  if(dybParameters::electronicsParametrization == kSingleExponential){
    //nonlin  = 1 - SingleExpElectronics(dybParameters::anchorEnergy);
    nonlin  = 1 - SingleExpElectronics(dybParameters::anchorEnergy)
                + SingleExpElectronics(eVis);
    //nonlin  = SingleExpElectronics(eVis-dybParameters::anchorEnergy);
  }
  if(dybParameters::electronicsParametrization == kDoubleExponential){
    nonlin  = 1 - DoubleExpElectronics(dybParameters::anchorEnergy)
                + DoubleExpElectronics(eVis);
  }
  return nonlin;
  //return 1;
}
double dybEnergyModel::SimpleEmpScintillator(double eTru){
  return (s_p0+s_p3*eTru)/(1+s_p1*exp(-s_p2*eTru));
}
double dybEnergyModel::LowECorrEmpScintillator(double eTru){
  double  lowECorr = 1 / (1+1.0*exp(-eTru/0.005)+ 0.25*exp(-eTru/0.02) );
  return lowECorr * (1+s_p3*eTru)/(1+s_p1*exp(-s_p2*eTru));
}
double dybEnergyModel::PhysicsScintillator(double eTru){

  if(s_kB==0) return 1.0;
  if(!s_isLoaded) Load();
  Update();
  int idx = int(eTru/s_samplingResol+0.5);
  if(idx < 0 || idx >= int(s_nSamples)) return 1.0;
  //cout<<idx<<endl;
  double cerenkNL = s_cer*s_cerenkovShape[idx]/8.49615/eTru;
  //cout<<"alive"<<endl;
  //cout<<idx<<' '<<s_kBResid<<endl;
  double quenchNL  =  s_kBResid    *s_quenchingShape1_lowKb[idx] 
                    +(1-s_kBResid) *s_quenchingShape1_higKb[idx];
  //cout<<"alive"<<endl;
  if(s_rad>0)
  { 
    double quench2NL =  s_kBResid    *s_quenchingShape2_lowKb[idx] 
                      +(1-s_kBResid) *s_quenchingShape2_higKb[idx];
    quenchNL = (1-s_rad)*quenchNL + s_rad * quench2NL; 
  }
  return quenchNL+cerenkNL;
}
double dybEnergyModel::SingleExpElectronics(double eVis){
  return s_alp1*exp(-eVis/s_tau1);
}
double dybEnergyModel::DoubleExpElectronics(double eVis){
  return s_alp1*exp(-eVis/s_tau1) + s_alp2*exp(-eVis/s_tau2);
}
double dybEnergyModel::PolynomialElectronics(double eVis){
  if(eVis > s_tau1) return 1-s_alp1;
  return 1-2*s_alp1*eVis/s_tau1+s_alp1*pow(eVis/s_tau1,2);
}
void dybEnergyModel::SaveCurves(){
  cout << " Scale = " << dybEnergyModel::s_p0    << endl;
  cout << " kB    = " << dybEnergyModel::s_p1    << endl;
  cout << " kC    = " << dybEnergyModel::s_p2    << endl;
  cout << " Rad   = " << dybEnergyModel::s_p3    << endl;
  std::cout << "  " << std::endl;
  cout << " Alpha = " << dybEnergyModel::s_alp1  << endl;
  cout << " Tau   = " << dybEnergyModel::s_tau1  << endl;
  cout << " Alp2  = " << dybEnergyModel::s_alp2  << endl;
  cout << " Tau2  = " << dybEnergyModel::s_tau2  << endl;
  //cout << dybSpectrum::s_n12Ratio << endl;
  cout << " GamS   = " << dybGammaPeak::s_gamScale << endl;
  
  TGraph elec = DrawElectronicsNL  ();
  TGraph eleS = DrawElectronScintNL();
  TGraph posS = DrawPositronScintNL();
  TGraph gamS = DrawGammaScintNL   ();
  TGraph alpS = DrawAlphaScintNL   ();
  TGraph eleF = DrawElectronFullNL ();
  TGraph posF = DrawPositronFullNL ();
  TGraph gamF = DrawGammaFullNL    ();
  TGraph alpF = DrawAlphaFullNL    ();
  string name = "output/curves/curves_"+dybParameters::toyKey+".root";
  TFile* nlFile = new TFile(name.c_str(),"recreate");
  elec.Write("electronicsNL");
  eleS.Write("electronScintNL");
  posS.Write("positronScintNL");
  gamS.Write("gammaScintNL");
  alpS.Write("alphaScintNL");
  eleF.Write("electronFullNL");
  posF.Write("positronFullNL");
  gamF.Write("gammaFullNL");
  alpF.Write("alphaFullNL");
  nlFile->Close();
  delete nlFile;
}
vector<double> dybEnergyModel::SampleElectronScintNL(int nSamples,double eMax)
{
  m_energySamples.clear();
  vector<double> electronScintNL;
  double deltaE = eMax/nSamples;
  double eTru;
  for(int i=0; i<nSamples; i++)
  {
    eTru = (i+1) * deltaE;
    if(eTru>eMax) break;
    m_energySamples.push_back(eTru);
    electronScintNL.push_back(ScintillatorNL(eTru));
  }
  return electronScintNL;
}
vector<double> dybEnergyModel::SampleAlphaScintNL(int nSamples,double eMax)
{
  m_energySamples.clear();
  vector<double> alphaScintNL;
  double deltaE = eMax/nSamples;
  double eTru;
  for(int i=0; i<nSamples; i++)
  {
    eTru = (i+1) * deltaE;
    if(eTru>eMax) break;
    m_energySamples.push_back(eTru);
    alphaScintNL.push_back(AlphaNL(eTru));
  }
  return alphaScintNL;
}
vector<double> dybEnergyModel::SampleElectronicsNL(int nSamples,double eMax)
{
  m_energySamples.clear();
  vector<double> electronicsNL;
  double deltaE = eMax/nSamples;
  double eTru;
  for(int i=0; i<nSamples; i++)
  {
    eTru = (i+1) * deltaE;
    if(eTru>eMax) break;
    m_energySamples.push_back(eTru);
    electronicsNL.push_back(ElectronicsNL(eTru));
  }
  return electronicsNL;
}
TGraph dybEnergyModel::DrawElectronScintNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue-2);
  m_energySamples.clear();
  vector<double> nl = SampleElectronScintNL(nSamples,eMax);
  for(int i=0; i<m_energySamples.size(); i++)
  {
    gr.SetPoint(i,m_energySamples[i],nl[i]);
  }
  return gr;
}
TGraph dybEnergyModel::DrawAlphaScintNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue-2);
  m_energySamples.clear();
  vector<double> nl = SampleAlphaScintNL(nSamples,eMax);
  for(int i=0; i<m_energySamples.size(); i++)
  {
    gr.SetPoint(i,m_energySamples[i],nl[i]);
  }
  return gr;
}
//vector<double> dybEnergyModel::SampleGammaScintNL(int nSamples)
//{
  //m_energySamples.clear();
  //vector<double> gammaScintNL;
  //for (int i=0; i<19; i++)
  //{
    //std::stringstream ss;ss<<i;
    //std::string pdfName = "hE" + ss.str();
    //double  eTrue = (i+1)*0.1;
    //if(i>8) eTrue = i - 8;
    //dybGammaPeak peak("name",pdfName,eTrue,eTrue);
    //peak.UpdateTheoNL();
    //gr.SetPoint(i-1,eTru,peak.GetTheoScintNL());
  //}
  //return gr;
//}
TGraph dybEnergyModel::DrawGammaScintNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue+1);
  for (int i=0; i<19; i++)
  {
    std::stringstream ss;ss<<i;
    std::string pdfName = "hE" + ss.str();
    double  energy = (i+1)*0.1;
    if(i>8) energy = i - 8;
    dybGammaPeak peak("name",pdfName,energy,energy);
    peak.UpdateTheoNL();
    gr.SetPoint(i-1,energy,peak.GetTheoScintNL());
    /*
    //Add anchor point
    if(i-8 < dybParameters::anchorEnergy)
        gr.SetPoint(i-1,energy,peak.GetTheoScintNL());
    else
        gr.SetPoint(i,energy,peak.GetTheoScintNL());
    if(i-8 < dybParameters::anchorEnergy && i+1-8>dybParameters::anchorEnergy){
        dybGammaPeak peak_anchor("n-H","hEnH" ,2.2233,2.2233);
        peak_anchor.UpdateTheoNL();
        gr.SetPoint(i,peak_anchor.GetEffectiveEnergy(),peak_anchor.GetTheoScintNL());
    }
    */
  }
  return gr;
}
vector<double> dybEnergyModel::SamplePositronScintNL(int nSamples,double eMax)
{
  dybGammaPeak ge68("ge68","hEGe",1.022,0.511);
  ge68.UpdateTheoNL();
  double ge68NL = ge68.GetTheoScintNL();
  
  m_energySamples.clear();
  vector<double> positronScintNL;
  
  ge68NL /= dybGammaPeak::s_gamScale;
  double deltaE = 12./nSamples;
  double eTru,eVis,eKin;
  for(int i=0; i<nSamples; i++)
  {
    eTru = i*deltaE + 1.022;
    if(eTru>12) break;
    eKin = eTru - 1.0221;
    eVis = 1.022*ge68NL + eKin*ScintillatorNL(eKin);
    m_energySamples.push_back(eTru);
    positronScintNL.push_back(eVis/eTru);
  }
  return positronScintNL;
}
TGraph dybEnergyModel::DrawPositronScintNL(int nSamples,double eMax)
{
	TGraph gr(0);
	vector<double> nl = SamplePositronScintNL(1000);
	for(int i=0; i<m_energySamples.size(); i++) {
	    gr.SetPoint(i,m_energySamples[i],nl[i]);
	}
	return gr;
}
TGraph dybEnergyModel::DrawElectronicsNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue-2);
  m_energySamples.clear();
  vector<double> nl = SampleElectronicsNL(nSamples,eMax);
  for(int i=0; i<m_energySamples.size(); i++)
  {
    gr.SetPoint(i,m_energySamples[i],nl[i]);
  }
  return gr;
}
TGraph dybEnergyModel::DrawElectronFullNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue+1);
  double deltaE = eMax/nSamples;
  for(int i=0; i<nSamples; i++)
  {
    double eTru = (i+1) * deltaE;
    double eVis = eTru*ScintillatorNL(eTru);
    double eRec = eVis*ElectronicsNL(eVis);
    gr.SetPoint(i,eTru,eRec/eTru);
  }
  return gr;
}
TGraph dybEnergyModel::DrawAlphaFullNL(int nSamples,double eMax)
{
  TGraph gr(0);
  gr.SetLineColor(kBlue+1);
  double deltaE = eMax/nSamples;
  for(int i=0; i<nSamples; i++)
  {
    double eTru = (i+1) * deltaE;
    double eVis = eTru*AlphaNL(eTru);
    double eRec = eVis*ElectronicsNL(eVis);
    gr.SetPoint(i,eTru,eRec/eTru);
  }
  return gr;
}
TGraph dybEnergyModel::DrawGammaFullNL(int nSamples,double eMax)
{
  TGraph scintG = DrawGammaScintNL();
  TGraph fullG(0);
  fullG.SetLineColor(kRed+1);
  for (int i=0; i<scintG.GetN(); i++)
  {
    double eTru,scintNL;
    scintG.GetPoint(i,eTru,scintNL);
    double eVis = eTru*scintNL;
    double eRec = eVis*ElectronicsNL(eVis);
    fullG.SetPoint(i,eTru,eRec/eTru);
  }
  return fullG;
}
vector<double> dybEnergyModel::SamplePositronFullNL(int nSamples,double eMax)
{
  vector<double> scintPositronNL = SamplePositronScintNL(nSamples);
  vector<double> fullPositronNL;
  for (int i=0; i<scintPositronNL.size(); i++)
  {
    double eTru = m_energySamples[i];
    double eVis = m_energySamples[i]*scintPositronNL[i];
    fullPositronNL.push_back(scintPositronNL[i]*ElectronicsNL(eVis));
  }
  return fullPositronNL;
  
}
vector<double> dybEnergyModel::SampleElectronFullNL(int nSamples,double eMax)
{
  vector<double> scintElectronNL = SampleElectronScintNL(nSamples);
  vector<double> fullElectronNL;
  for (int i=0; i<scintElectronNL.size(); i++)
  {
    double eTru = m_energySamples[i];
    double eVis = m_energySamples[i]*scintElectronNL[i];
    fullElectronNL.push_back(scintElectronNL[i]*ElectronicsNL(eVis));
  }
  return fullElectronNL;
}
vector<double> dybEnergyModel::SampleAlphaFullNL(int nSamples,double eMax)
{
  vector<double> scintAlphaNL = SampleAlphaScintNL(nSamples);
  vector<double> fullAlphaNL;
  for (int i=0; i<scintAlphaNL.size(); i++)
  {
    double eTru = m_energySamples[i];
    double eVis = m_energySamples[i]*scintAlphaNL[i];
    fullAlphaNL.push_back(scintAlphaNL[i]*ElectronicsNL(eVis));
  }
  return fullAlphaNL;
}
TGraph dybEnergyModel::DrawPositronFullNL(int nSamples,double eMax)
{
  TGraph gr(0);
  vector<double> nl = SamplePositronFullNL(nSamples);
  for(int i=0; i<m_energySamples.size(); i++)
    gr.SetPoint(i,m_energySamples[i],nl[i]);
  return gr;
}

// Initialize static constant members
const double dybEnergyModel::s_kBMax = 24.9;
const double dybEnergyModel::s_kBMax_alpha = 24.9;
const double dybEnergyModel::s_kBMin = 4.0;
const double dybEnergyModel::s_kBMin_alpha = 4.0;
const double dybEnergyModel::s_samplingRange = 20;
const double dybEnergyModel::s_samplingResol = 0.001;
