#include "dybLSData.h"

double dybLSData::s_lsScale = 1.0;
dybLSData::dybLSData(string groupName) :
m_data(0)
{
  m_groupName = groupName;
}
dybLSData::~dybLSData()
{
  //delete m_fit;
}
void  dybLSData::LoadData(std::string fileName)
{
  std::cout << " ----> Reading " << m_groupName << " LS data from " << fileName << std::endl;
  m_scale = 1;
  ifstream infile(fileName.c_str());
  int i = 0;
  double energy,nl,nlError;
  while (infile >> energy >> nl >> nlError)
  {
    //std::cout<<i<<std::endl;
    if(m_groupName.find("LBNL")!= std::string::npos) 
    {
      //nlError = 0.0015/energy + 0.006;
      //nlError = 0.002/energy + 0.006;
    }
    //std::cout<<"Before GetPoint!!! i="<<i<<" enregy="<<energy<<" nl="<<nl<<std::endl;    
    m_data.SetPoint(i,energy,nl);
    m_data.SetPointError(i,0,nlError);
    i++;
  }
  /*
  m_fit = new TF1("fit", this, &dybLSData::FitF,0,60,1);
  m_fit->SetParameter(0,1.0);
  m_fit->SetNpx(10000);
  */
  std::cout << " LS data initialized <-----" << std::endl;
}
double dybLSData::GetChi2(int nDoF)
{
  /* 
  m_data.Fit(m_fit,"Q","");
  m_scale = m_fit->GetParameter(0);
  m_fit->SetNpx(10000);
  double chi2  = m_fit->GetChisquare();
  if(nDoF>0) 
  {
    m_nData = m_data.GetN();
    chi2 /= double(m_nData - nDoF);
  }
  */
  //*******************//
  double chi2 = 0;
  for (int i = 0; i < m_data.GetN(); i++)
  {
    double energy,nl,nlError;
    m_data.GetPoint(i,energy,nl);
    nlError = m_data.GetErrorY(i);
    double nlTest = dybEnergyModel::ScintillatorNL(energy);
    double lsScaleTest = s_lsScale;
    chi2 += pow( (nl-nlTest*lsScaleTest)/(nlError) ,2);
  }
  if(nDoF>0)
  {
    chi2 /= double(m_data.GetN() - nDoF);
  }
  //*****************//
  return chi2;
}
double dybLSData::FitF(double *x, double *par)
{
  return par[0] * dybEnergyModel::ScintillatorNL(x[0]);
}
/*
TGraphErrors dybLSData::Plot(bool writeToFile)
{
  TGraphErrors gr(0);
  gr.SetMarkerStyle(20);
  gr.SetMarkerSize (0.8);
  gr.SetMarkerColor(kBlue+1);
  gr.SetLineColor(kBlue+1);
  string title = m_groupName+" LS Data;Electron energy [MeV];Scintillator non-linearity";
  gr.SetTitle(title.c_str());
  m_fit->SetLineWidth(2);
  m_fit->SetLineColor(kRed+1);
  GetChi2();
  //gr.SetMarkerSize(0.8);
  double energy,nl,nlError;
  for (int i = 0; i < m_data.GetN(); i++)
  {
    m_data.GetPoint(i,energy,nl);
    nlError = m_data.GetErrorY(i);
    gr.SetPoint(i,energy,nl/m_scale);
    gr.SetPointError(i,0,nlError/m_scale);
  }
  if(m_groupName.find("IHEP")!= std::string::npos){
    gr.Fit(m_fit,"Q0","",0,1.2);
  }
  else {
    //gr.Fit(m_fit,"Q","",0,1.2);
    gr.Fit(m_fit,"Q","",0,60);
  }
  m_fit->SetLineColor(kRed+1);
  m_fit->SetLineWidth(2);
  m_fit->SetNpx(10000);
  //gr.GetYaxis()->SetRangeUser(0.88,1.15);
  //gr.GetYaxis()->SetRangeUser(0.75,1.08);
  //gr.GetYaxis()->SetRangeUser(0.96,1.05);
  //gr.GetListOfFunctions()->Add(m_fit);
  gr.GetXaxis()->SetLimits(0,1.2);
  //gr.GetXaxis()->SetLimits(0,60);
  TString name = dybParameters::title + ": " + m_groupName;
  //gr.SetTitle(name+" LS Data;True Electron Energy [MeV];Scintillator Non-Linearity");
  //gr.SetTitle("Benchtop LS Data - Scintillator NL;Electron energy [MeV];Scintillator non-Linearity");
  gr.SetTitle("NuWa k_{B} = 6, best fit standalone k_{B} = 4.74;Electron energy [MeV];Quenching non-Linearity");
  //gr.SetTitle("Benchtop LS Data NOT Included in Fit;Electron Energy [MeV];Scintillator Non-Linearity");
  if(writeToFile)
  {
    TCanvas* tmpC = new TCanvas("tmpC","",800,520);
    gr.Draw("APZ");
    m_fit->Draw("same");
    gr.Draw("PZ");
    string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_ls"+m_groupName+"."+dybParameters::plotFormat;
    tmpC->SaveAs(plotName.c_str());
    delete tmpC;
  }
  return gr;
}
*/
//************//
TGraphErrors dybLSData::Plot(bool writeToFile)
{
  std::cout<<"Running dybLSData::Plot!!!"<<std::endl; 
  TGraphErrors gr(0);
  gr.SetMarkerStyle(20);
  gr.SetMarkerSize (0.8);
  gr.SetMarkerColor(kBlue+1);
  gr.SetLineColor(kBlue+1);
  string title = m_groupName+" LS Data;Electron energy [MeV];Scintillator non-linearity";
  gr.SetTitle(title.c_str());
  gr.SetMarkerStyle(20);
  gr.SetMarkerColor(kBlue+1);
  gr.SetLineColor(kBlue+1);
  gr.SetLineWidth(3);
  gr.SetFillColor(kBlue-8);
  for (int i = 0; i < m_data.GetN(); i++)
  {
    double energy,nl,nlError;
    m_data.GetPoint(i,energy,nl);
    //std::cout<<"After GetPoint!!! i="<<i<<" enregy="<<energy<<" nl="<<nl<<std::endl;
    nlError = m_data.GetErrorY(i);
    gr.SetPoint(i,energy,nl);
    gr.SetPointError(i,0,nlError);
  }
 
  TGraphErrors gr_fit(0);
  gr_fit.SetMarkerStyle(20);
  gr_fit.SetMarkerSize (0.8);
  gr_fit.SetMarkerColor(kRed+1);
  gr_fit.SetLineColor(kRed+1); 
  for (int i = 0; i < 1100; i++)
  { 
    double energy_fit,nl_fit;
    energy_fit = 0.001*(i+100);
    nl_fit = dybEnergyModel::ScintillatorNL(energy_fit);
    nl_fit = nl_fit*s_lsScale;
    gr_fit.SetPoint(i,energy_fit,nl_fit);
  }
 
  if(writeToFile)
  {
    TCanvas* tmpC = new TCanvas("tmpC","",800,520);
    gr.Draw("APZ");
    gr_fit.Draw("PLsame");
    gr.Draw("PZ");
    string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_ls"+m_groupName+"."+dybParameters::plotFormat;
    tmpC->SaveAs(plotName.c_str());
    delete tmpC;
  }

  return gr; 
}
//****************//  
void dybLSData::GenToyMC()
{
  std::cout << " ------> Generating " << dybParameters::nToy << " LS toy MC samples " << std::endl;
  TRandom3 rand;
  for (int toyIdx=0; toyIdx<dybParameters::nToy; toyIdx++)
  {
    stringstream ss; ss<<toyIdx;
    std::string toyName = dybParameters::toyFolder;
    toyName += "ls" + m_groupName + "Toy_" + dybParameters::toyKey + "_" +  ss.str() + ".dat";
    ofstream toyFile(toyName.c_str());
    for(int i=0;i<m_data.GetN();i++)
    {
      double eTru,nl;
      m_data.GetPoint(i,eTru,nl);
      double theoNl  = dybEnergyModel::ScintillatorNL(eTru);
      double nlError = m_data.GetErrorY(i);
      double toyETru = rand.Gaus(eTru,  0.01);
      double toyNl   = rand.Gaus(theoNl,nlError);
             toyETru = rand.Gaus(eTru,  0.01);
      //std::cout << " ------------> " << std::endl;
      //std::cout << eRec << " +- " << eRecError << std::endl;
      //std::cout << toyERec << std::endl;
      toyFile << toyETru << " " << toyNl << " " << nlError << endl;
    }
    toyFile.close();
  }
}
