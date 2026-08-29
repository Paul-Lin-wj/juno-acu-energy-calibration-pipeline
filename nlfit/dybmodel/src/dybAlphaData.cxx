#include "dybAlphaData.h"

dybAlphaData::dybAlphaData()
{
  cout << " -----> Initializing alpha peaks " << endl;
  cout << " finished alpha data initialization <------ " << endl;
}
void dybAlphaData::AddPeak(string name,double eTru)
{
  std::cout << " adding " << name << " peak" << std::endl;
  dybAlphaPeak peak(name.c_str(),eTru);
  m_data.push_back(peak);
}
void dybAlphaData::LoadData(string fileName)
{
	std::cout << " Loading Alpha data " << std::endl;
  m_data.clear();
  AddPeak("^{210}Po",5.304);
  AddPeak("^{215}Po",7.386);
  AddPeak("^{214}Po",7.686);
  AddPeak("^{212}Po",8.784);
  std::cout << " -----> Reading alpha data from " << fileName << std::endl;
  ifstream infile(fileName.c_str());
  double eRec,eRecError;
  int i=0;
  while (infile >> eRec >> eRecError)
  {
    if(i>=m_data.size())
      std::cout << " ERROR: Data file contains more alpha peaks than initialized" << std::endl;
    m_data[i].SetERec     (eRec);
    m_data[i].SetERecError(eRecError);
    i++;
  }
  if(i!=m_data.size())
    std::cout << " ERROR: Data file contains less alpha peaks than initialized" << std::endl;
}
double dybAlphaData::GetChi2(int nDoF)
{
  double chi2 = 0;
  vector<dybAlphaPeak>::iterator peakItr = m_data.begin();
  for(;peakItr!=m_data.end();peakItr++)
  {
            peakItr->UpdateTheoNL();
    chi2 += peakItr->GetChi2     ();
  }
  if(nDoF>0) 
  {
    chi2 /= double(m_data.size() - nDoF);
    m_nData = m_data.size();
  }
  return chi2;
}
void dybAlphaData::Plot(bool writeToFile)
{
	TGraphErrors* peaksScint    = new TGraphErrors;
	TGraphErrors* peaksScintR   = new TGraphErrors;
	TGraphErrors* peaksFull     = new TGraphErrors;
	peaksFull   ->SetLineColor  (kBlue+1);
	peaksScint  ->SetLineColor  (kBlue+1);
	peaksScintR ->SetLineColor  (kBlue+1);
	peaksFull   ->SetMarkerColor(kBlue+1);
	peaksScint  ->SetMarkerColor(kBlue+1);
	peaksScintR ->SetMarkerColor(kBlue+1);
	peaksFull   ->SetMarkerStyle(20);
	peaksScint  ->SetMarkerStyle(20);
	peaksScintR ->SetMarkerStyle(20);
	peaksFull   ->SetMarkerSize(1.2);
	peaksScint  ->SetMarkerSize(1.2);
	peaksScintR ->SetMarkerSize(1.2);
	vector<dybAlphaPeak>::iterator peakItr = m_data.begin();
	int pointIdx    = 0;
	for(;peakItr!=m_data.end();peakItr++)
	{
		peakItr->UpdateTheoNL();
		peakItr->UpdateDataNL();
		double eTru     = peakItr->GetETru();
		double error    = peakItr->GetERecError();
		//error = 0.2;
		std::cout << " ----- error " << error << std::endl;
		double nlScint  = peakItr->GetDataScintNL();
		double nlFull   = peakItr->GetDataFullNL();
		double eVis     = peakItr->GetEVis();
		double eRec     = peakItr->GetERec();
		double eRecPred = peakItr->GetTheoFullNL()*eTru;
		//peaksFull   ->SetPoint     (pointIdx   ,eTru,eRec/eTru);
		peaksFull  ->SetPoint     (pointIdx,eTru,eRec/eTru);
		peaksFull  ->SetPointError(pointIdx,0,   eRec/eTru*error);
		peaksScint ->SetPoint     (pointIdx,eTru,nlScint);
		peaksScint ->SetPointError(pointIdx,0,nlScint*error);
		peaksScintR->SetPoint     (pointIdx,eTru,eRec/eRecPred);
		peaksScintR->SetPointError(pointIdx,0,error);
		pointIdx++;
	}
	TMultiGraph* allPeaks = new TMultiGraph;
	allPeaks->Add(peaksScint,  "PZ");
	TGraph alphaScintNL = dybEnergyModel::DrawAlphaScintNL();
	TGraph alphaFullNL  = dybEnergyModel::DrawAlphaFullNL();
	TCanvas* tmpC1 = new TCanvas("tmpC1","",800,520);
	TCanvas* tmpC0 = new TCanvas("tmpC0","",800,520);
	tmpC1->cd();
	double chi2 = GetChi2();
	int nPeaks  = m_data.size();
	stringstream ssChi2;ssChi2.precision(3);ssChi2<<chi2;
	stringstream ssPeak;ssPeak<<nPeaks;
	TString name = dybParameters::title;
	TString gamTitle = "Alpha calibration data: #chi^{2} = "+ssChi2.str()+" / "+ssPeak.str()+" peaks;Effective Single #gamma Energy [MeV];Scintillator Non-Linearity";
	peaksScint->SetTitle(gamTitle);
	peaksScint->Draw("APZ");
	alphaScintNL.SetLineColor(kRed+1);
	alphaScintNL.SetLineWidth(2);
	alphaScintNL.Draw("C");
	peaksScint->Draw("PZ");
	TLegend* leg=new TLegend(0.18,0.68,0.58,0.88);
	leg->SetBorderSize(0);
	leg->SetFillColor(-1);
	TLegendEntry *leS = leg->AddEntry(peaksScint,   "Alpha data","PE");
	TLegendEntry *leF = leg->AddEntry(&alphaScintNL,"Best Fit Model","L");
	leS->SetLineColor  (kBlue-2);
	leg->SetTextSize(19);
	leg->Draw();
	TLegend* legB=new TLegend(0.68,0.16,0.88,0.4);
	legB->SetBorderSize(0);
	legB->SetFillStyle(-1);
	legB->SetFillColor(-1);
	TLegendEntry *leSB = legB->AddEntry((TObject*)0," "," ");
	TLegendEntry *leFB = legB->AddEntry((TObject*)0," "," ");
	legB->SetTextSize(19);
	legB->Draw();
	/// raw data
	tmpC0->cd();
	peaksFull->GetXaxis()->SetRangeUser(0,10);
	peaksFull->GetXaxis()->SetLimits   (0,10);
	peaksFull->GetYaxis()->SetRangeUser(0.0,0.2);
	peaksFull->SetTitle("Raw alpha data;Alpha energy [MeV];Non-linearity");
	peaksFull->Draw("APZ");
	alphaFullNL.SetLineColor(kRed+2);
	alphaFullNL.SetLineWidth(2);
	alphaFullNL.Draw("C");
	peaksFull->Draw("PZ");
	/// split canvas
	TCanvas* tmpC3 = new TCanvas("tmpC","",800,520);
	TPad *pad1 = new TPad("pad1","pad1",0,0.3,1,1);
	pad1->SetBottomMargin(0);
	pad1->Draw();
	TPad *pad2 = new TPad("pad2","pad2",0,0,1,0.3);
	pad2->SetTopMargin(0);
	pad2->SetBottomMargin(0.35);
	//pad2->SetGridy();
	pad2->Draw();
	pad1->cd();
	float oldSize = gStyle->GetTitleSize("T");
	gStyle->SetTitleSize(0.08,"T");  
	
	peaksScint->GetXaxis()->SetRangeUser(0,10);
	peaksScint->GetXaxis()->SetLimits   (0,10);
	peaksScint->GetYaxis()->SetRangeUser(0.0,0.2);

	peaksScint->GetYaxis()->SetLabelSize(19);
	peaksScint->GetYaxis()->SetTitleSize(21);
	peaksScint->Draw("APZ");
    alphaScintNL.Draw("C");
    peaksScint->Draw("PZ");
    
	pad2->cd();
	peaksScintR->GetYaxis()->SetNdivisions(505);
	peaksScintR->SetMinimum(0.96);
	peaksScintR->SetMaximum(1.04);
	peaksScintR->GetXaxis()->SetRangeUser(0,9);
	peaksScintR->GetXaxis()->SetLimits   (0,9);
	
	peaksScintR->GetXaxis()->SetTickLength (0.1);  
	peaksScintR->GetXaxis()->SetTitleSize(21);  
	peaksScintR->GetXaxis()->SetLabelSize(19);  
	peaksScintR->GetYaxis()->SetLabelSize(17);  
	peaksScintR->SetTitle(";Alpha energy [MeV]");
	peaksScintR->SetMarkerSize(1.0);
	peaksScintR->Draw("APZ");
	TF1 oneF("lineF","pol0",0,20);
	oneF.SetLineWidth(1);
	oneF.SetParameter(0,1); 
	oneF.SetLineColor(kRed+3);
	oneF.Draw("same");
	peaksScintR->Draw("PZ");
	peaksScintR->SetMarkerSize(1.2);
	  
    for(peakItr = m_data.begin();peakItr!=m_data.end();peakItr++)
    {
		TLatex latex;
		double eTru    = peakItr->GetETru();
		double eVis    = peakItr->GetEVis();
		double nlFull  = peakItr->GetDataFullNL();
		double nlScint = peakItr->GetDataScintNL();
		double nlElec  = peakItr->GetERec()/peakItr->GetEVis();
		string name    = peakItr->GetName();
		latex.SetTextSize(0.035);
		latex.SetTextColor(kBlue+2);
		latex.SetTextAlign(13);  //align at top left
		tmpC1->cd();
		latex.DrawLatex(eTru+0.08,nlScint-0.006,name.c_str());
		tmpC0->cd();
		if(fabs(eTru-0.8)<0.1)
			latex.DrawLatex(eTru+0.02,nlFull-0.01,name.c_str());
		else
			latex.DrawLatex(eTru+0.08,nlFull-0.006,name.c_str());
		tmpC3->cd();
		pad1->cd();
		latex.SetTextSize(0.045);
		latex.DrawLatex(eTru+0.08,nlScint-0.008,name.c_str());
		latex.SetTextSize(0.035);
		latex.SetTextAlign(23); 
    }
    string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_alpha."+dybParameters::plotFormat;
    tmpC1->SaveAs(plotName.c_str());
    plotName = dybParameters::plotFolder+dybParameters::toyKey+"_alpha_ratio."+dybParameters::plotFormat;
    tmpC3->SaveAs(plotName.c_str());
    plotName = dybParameters::plotFolder+dybParameters::toyKey+"_alpha_raw."+dybParameters::plotFormat;
    tmpC0->SaveAs(plotName.c_str());
    delete tmpC1;
    delete tmpC3;
    delete tmpC0;
    //string outname = "output/alphas/alphas_"+dybParameters::toyKey+".root";
    //TFile* alphaFile = new TFile(outname.c_str(),"recreate");
	//peaksScint    ->Write("peaksScint")   ;
	//peaksScintR   ->Write("peaksScintR")  ;
	//peaksElec      ->Write("peaksElec")     ;
	//peaksFull      ->Write("peaksFull")     ;
    //alphaFile->Close();
    //delete alphaFile;
}
TGraphErrors dybAlphaData::PlotPeaks(int type)
{
  cout << " ---> Intializing Alpha data " << endl;
  TGraphErrors gr(0);
  gr.SetLineColor  (kBlue+2);
  gr.SetMarkerColor(kBlue+2);
  gr.SetMarkerStyle(10);
  gr.SetMarkerSize (0.6);
  vector<dybAlphaPeak>::iterator peakItr = m_data.begin();
  int pointIdx=0;
  for(;peakItr!=m_data.end();peakItr++)
  {
    std::cout << peakItr->GetName() << std::endl;
    double energy   = peakItr->GetETru();
    double error    = peakItr->GetERecError();
    double nl       = 1;
    peakItr->UpdateDataNL();
    if(type==1) nl = peakItr->GetDataScintNL();
    if(type==2) nl = peakItr->GetDataFullNL ();
    if(type==3) nl = peakItr->GetTheoScintNL();
    if(type==4) nl = peakItr->GetTheoFullNL ();
    std::cout << " nl = " << nl << std::endl;
    std::cout << " error = " << error << std::endl;
    gr.SetPoint     (pointIdx,energy,nl);
    gr.SetPointError(pointIdx,0,nl*error);
    pointIdx++;
  }
  return gr;
}
void dybAlphaData::GenToyMC()
{
}
