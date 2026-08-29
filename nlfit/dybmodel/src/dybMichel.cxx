#include "dybMichel.h"

dybMichel::dybMichel() 
{
}
void  dybMichel::LoadData(std::string fileName)
{
  std::cout << " ----> Reading michel data from " << fileName << std::endl;
  m_michelEnergy = 53.;
  //m_data         = 1.034;
  //m_dataE        = 0.01;
  m_data         = 1.029;
  m_dataE        = 0.0075;
  m_nData        = 1;
  std::cout << " Michel  data initialized <-----" << std::endl;
}
double dybMichel::GetChi2(int nDoF)
{
  double eVis = m_michelEnergy*dybEnergyModel::ScintillatorNL(m_michelEnergy);
  double eRec = eVis          *dybEnergyModel::ElectronicsNL (eVis);
    
  double fullNL = eRec/m_michelEnergy;
  double chi2 = pow( (m_data-fullNL)/m_dataE ,2);
  //if(nDoF>0) 
  //{
    //chi2 /= double(m_nData - nDoF);
  //}
  return chi2;
}
TGraphErrors dybMichel::Plot(bool writeToFile)
{
  TGraphErrors gr(0);
  gr.SetMarkerStyle(20);
  gr.SetMarkerSize (1.2);
  gr.SetMarkerColor(kBlue-2);
  gr.SetLineColor  (kBlue-2);
  string title = "Michel Electron Data;Electron energy [MeV];Full Non-Linearity";
  gr.SetTitle(title.c_str());
  TGraph electronNL = dybEnergyModel::DrawElectronFullNL(10000,60);
  gr.SetLineWidth(2);
  electronNL.SetLineWidth(2);
  electronNL.SetLineColor(kRed-2);
  gr.SetPoint     (0,m_michelEnergy,m_data );
  gr.SetPointError(0,0,             m_dataE);
  electronNL.GetYaxis()->SetRangeUser(0.9,1.1);
  electronNL.GetXaxis()->SetRangeUser(0,55);
  electronNL.SetTitle(title.c_str());
  if(writeToFile)
  {
    TCanvas* tmpC = new TCanvas("tmpC","",800,520);
    tmpC->SetGridy();
    electronNL.Draw("AC");
    gr.Draw("PZ");
    TLegend* leg=new TLegend(0.5,0.16,0.88,0.4);
    leg->SetBorderSize(0);
    leg->SetFillColor(-1);
    TLegendEntry *leS = leg->AddEntry(&gr,"#splitline{Energy Scale from}{Edge in Michel Spectrum}","PE");
    //leg->AddEntry(&gr,"Edge in Michel Spectrum"," ");
    leg->AddEntry(&electronNL,"Best Fit Model","L");
    leS->SetLineColor(kBlue-2);
    leS->SetLineWidth(2);
    leg->SetTextSize(0.04);
    leg->Draw();
    string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_michel."+dybParameters::plotFormat;
    tmpC->SaveAs(plotName.c_str());
    delete tmpC;
  }
  return gr;
}
void dybMichel::GenToyMC()
{
  //std::cout << " ------> Generating " << dybParameters::nToy << " LS toy MC samples " << std::endl;
  //TRandom3 rand;
  //for (int toyIdx=0; toyIdx<dybParameters::nToy; toyIdx++)
  //{
    //stringstream ss; ss<<toyIdx;
    //std::string toyName = dybParameters::toyFolder;
    //toyName += "ls" + m_groupName + "Toy_" + dybParameters::toyKey + "_" +  ss.str() + ".dat";
    //ofstream toyFile(toyName.c_str());
    //for(int i=0;i<m_data.GetN();i++)
    //{
      //double eTru,nl;
      //m_data.GetPoint(i,eTru,nl);
      //double theoNl  = dybEnergyModel::ScintillatorNL(eTru);
      //double nlError = m_data.GetErrorY(i);
      //double toyETru = rand.Gaus(eTru,  0.01);
      //double toyNl   = rand.Gaus(theoNl,nlError);
             //toyETru = rand.Gaus(eTru,  0.01);
      ////std::cout << " ------------> " << std::endl;
      ////std::cout << eRec << " +- " << eRecError << std::endl;
      ////std::cout << toyERec << std::endl;
      //toyFile << toyETru << " " << toyNl << " " << nlError << endl;
    //}
    //toyFile.close();
  //}
}
