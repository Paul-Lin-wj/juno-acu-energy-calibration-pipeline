#include "dybFadcData.h"
#include "dybEnergyModel.h"

double dybFadcData::s_fadcNor = 1.0;
double dybFadcData::s_fadcRes = 0.;
dybFadcData::dybFadcData()
{
  
}
dybFadcData::~dybFadcData()
{
  //delete m_fit;
}
void dybFadcData::LoadData(string fileName)
{
  std::cout << " ----> Reading FADC data from " << fileName << std::endl;
  //m_scale = 1;
  ifstream infile(fileName.c_str());
 
  int i = 0;
  double energy,nl,nlError;
  while (infile >> energy >> nl >> nlError)
  {
    if(energy>9.2) break;
    m_energy       [i] = energy;
    m_adNonlin     [i] = nl;
    m_adNonlinError[i] = nlError;
    m_adNonlinError[i] = 0.001; 
    i++;
  }
   m_nData = i;
  std::cout << " FADC data initialized <-----" << std::endl;
  
}
void dybFadcData::LoadToyMC(string fileName)
{
  
}
double dybFadcData::GetChi2(int nDoF)
{
  double chi2 = 0;
  TGraph g_fadcRes = fadcResCorr();
  for (int i = 0; i < m_nData; i++)
  {
    double nlTest = dybEnergyModel::ElectronicsNL(m_energy[i]);
    double delta_fadcRes = (s_fadcRes-dybParameters::fadcRes)/dybParameters::fadcResError;
    chi2 += pow( (m_adNonlin[i]*s_fadcNor*(1+delta_fadcRes*0.5*(g_fadcRes.Eval(m_energy[i])-1))-nlTest)/(m_adNonlinError[i]) ,2);
  }
  if(nDoF>0) 
  {
    chi2 /= double(m_nData - nDoF);
  }
  return chi2;
}
void dybFadcData::GenToyMC()
{
  
}
double dybFadcData::FitF(double *x, double *par)
{
  return par[0] * dybEnergyModel::ElectronicsNL(x[0]);
}
TGraphErrors dybFadcData::Plot(bool writeToFile)
{
  std::cout<<"Running TGraphErrors dybFadcData::Plot!!!"<<std::endl;
  TGraphErrors gr(0);
  gr.SetMarkerStyle(20);
  gr.SetMarkerSize (0.8);
  gr.SetMarkerColor(kBlue+2);
  gr.SetLineColor(kBlue+2);
  string title = "FADC Data;Visible energy [MeV];Electronics non-linearity";
  gr.SetTitle(title.c_str());
  gr.SetMarkerStyle(20);
  gr.SetMarkerColor(kBlue+1);
  gr.SetLineColor(kBlue+1);
  gr.SetLineWidth(3);
  gr.SetFillColor(kBlue-8);
  TGraph g_fadcRes = fadcResCorr();
  //double nl_show[18] = {1.08086,1.07459,1.0653,1.05837,1.05166,1.04542,1.0402,1.03532,1.03215,1.02886,1.02341,1.01422,1.00757,1.0048,1.00137,0.999847,0.999781,0.998254};//scale to nGd
  double nl_show[18] = {1.01513,1.015,1.01339,1.01422,1.01261,1.01126,1.01016,1.00894,1.00894,1.00848,1.00698,1.00554,1.00234,1.00195,1.00053,0.999941,0.999536,0.998658};//scale to nGd
  for (int i = 0; i < m_nData; i++)
  {
    double delta_fadcRes = (s_fadcRes-dybParameters::fadcRes)/dybParameters::fadcResError;
    gr.SetPoint(i,m_energy[i],nl_show[i]);
    gr.SetPointError(i,0,0.002);
  }

  TGraphErrors gr_fit(0);
  gr_fit.SetMarkerStyle(20);
  gr_fit.SetMarkerSize (0.8);
  gr_fit.SetMarkerColor(kRed+1);
  gr_fit.SetLineColor(kRed+1);
  for (int i = 0; i < 10000; i++)
  {
    double energy_fit,nl_fit;
    energy_fit = 0.001*i;
    nl_fit = dybEnergyModel::ElectronicsNL(energy_fit);
    gr_fit.SetPoint(i,energy_fit,nl_fit);
  }

  if(writeToFile)
  {
    TCanvas* tmpC = new TCanvas("tmpC","",800,520);
    gr.Draw("APZ");
    gr_fit.Draw("PLsame");
    gr.GetXaxis()->SetTitleFont(132);
    gr.GetXaxis()->SetTitleSize(0.05);
    gr.GetXaxis()->SetLabelFont(132);
    gr.GetXaxis()->SetLabelSize(0.05);
    gr.GetYaxis()->SetTitleFont(132);
    gr.GetYaxis()->SetTitleSize(0.05);
    gr.GetYaxis()->SetLabelFont(132);
    gr.GetYaxis()->SetLabelSize(0.05);
    gr.Draw("PZ");
    string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_fadc"+"."+dybParameters::plotFormat;
    tmpC->SaveAs(plotName.c_str());
    delete tmpC;
  }

  return gr;
}

TGraph dybFadcData::fadcResCorr()  {
	TGraph g_fadcRes(0);
	double energy_fadcRes[18] = {0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5,2.75,3.375,4.375,5.375,6.375,7.375,8.125,8.625,9.125};
 	double ratio_fadcRes[18] = {1.00198,1.00194,1.00182,1.00172,1.00162,1.00152,1.00146,1.00141,1.00135,1.00124,1.00103,1.00065,1.00069,1.00026,1.00022,0.999975,0.999991,0.999765};//scale to nGd
	for(int i=0; i<18; i++) {
    		g_fadcRes.SetPoint(i,energy_fadcRes[i],ratio_fadcRes[i]);
	}
	return g_fadcRes;
}

