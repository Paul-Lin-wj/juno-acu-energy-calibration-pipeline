#include "dybGammaData.h"

namespace {

void StyleGammaRatioGraph(TGraphErrors* graph, bool multipleMarker)
{
	graph->SetLineColor(kBlue+1);
	graph->SetMarkerColor(multipleMarker ? kWhite : kBlue+1);
	graph->SetMarkerStyle(20);
	graph->SetMarkerSize(multipleMarker ? 0.5 : 1.1);
}

void DrawGammaRatioCanvas(TCanvas* canvas,
                          TGraphErrors* peaksTop,
                          TGraphErrors* peaksTopM,
                          TGraphErrors* peaksRatio,
                          TGraphErrors* peaksRatioMR,
                          TGraph& gammaModel,
                          TGraph& positronModel,
                          TLegend* legData,
                          TLegend* legDataB,
                          const char* topYTitle,
                          double topYMin,
                          double topYMax,
                          TPad*& outPad1)
{
	canvas->cd();
	TPad* pad1 = new TPad(Form("%s_pad1", canvas->GetName()), "pad1", 0, 0.5, 1, 1);
	pad1->SetBottomMargin(0);
	pad1->Draw();
	TPad* pad2 = new TPad(Form("%s_pad2", canvas->GetName()), "pad2", 0, 0, 1, 0.5);
	pad2->SetTopMargin(0);
	pad2->SetBottomMargin(0.35);
	pad2->SetGridy();
	pad2->Draw();
	outPad1 = pad1;

	pad1->cd();
	peaksTop->GetXaxis()->SetRangeUser(0, 9);
	peaksTop->GetXaxis()->SetLimits(0, 9);
	peaksTop->GetYaxis()->SetLimits(0.88, 1.1);
	peaksRatio->GetYaxis()->SetTitleOffset(1.1);
	peaksTop->GetYaxis()->SetLabelSize(18);
	peaksTop->GetYaxis()->SetTitleSize(21);
	peaksTop->GetYaxis()->SetRangeUser(topYMin, topYMax);
	peaksTop->GetXaxis()->SetTickLength(0.05);
	peaksTop->SetTitle(Form(" ;Effective single #gamma energy [MeV];%s", topYTitle));
	peaksTop->Draw("APZ");

	gammaModel.SetMarkerStyle(0);
	gammaModel.SetLineColor(kRed+1);
	gammaModel.SetLineWidth(2);
	gammaModel.SetLineStyle(1);
	gammaModel.Draw("C");

	positronModel.SetMarkerStyle(0);
	positronModel.SetLineColor(kRed+1);
	positronModel.SetLineWidth(2);
	positronModel.SetLineStyle(2);
	positronModel.Draw("C same");

	peaksTop->Draw("PZ");
	peaksTopM->Draw("PZ");
	legData->Draw();
	legDataB->Draw();

	pad2->cd();
	peaksRatio->GetYaxis()->SetNdivisions(505);
	peaksRatio->SetMinimum(0.9799);
	peaksRatio->SetMaximum(1.0201);
	peaksRatio->GetXaxis()->SetRangeUser(0, 9);
	peaksRatio->GetXaxis()->SetLimits(0, 9);
	peaksRatio->GetYaxis()->SetTitleOffset(1.1);
	peaksRatio->GetXaxis()->SetTickLength(0.1);
	peaksRatio->GetXaxis()->SetTitleSize(21);
	peaksRatio->GetXaxis()->SetLabelSize(19);
	peaksRatio->GetYaxis()->SetLabelSize(18);
	peaksRatio->SetTitle(";Effective True Energy [MeV];#gamma: Data/best fit");
	peaksRatio->GetXaxis()->SetTitleOffset(3.0);
	peaksRatio->Draw("APZ");

	static Int_t ratioBandFillColor = 0;
	if(ratioBandFillColor == 0)
	{
		TColor* bandColor = new TColor(10001, 1.0, 0.0, 0.0, "gammaRatioBand", 0.25);
		ratioBandFillColor = bandColor->GetNumber();
	}
	TBox* ratioBand = new TBox(0.0, 0.99, 9.0, 1.01);
	ratioBand->SetFillColor(ratioBandFillColor);
	ratioBand->SetFillStyle(1001);
	ratioBand->SetLineWidth(0);
	ratioBand->Draw("same");

	TF1* oneF = new TF1(Form("lineF_%s", canvas->GetName()), "pol0", 0, 20);
	oneF->SetLineWidth(2);
	oneF->SetParameter(0, 1);
	oneF->SetLineColor(kRed+1);
	oneF->Draw("same");
	peaksRatio->Draw("PZ");
	peaksRatioMR->Draw("PZ");
}

void ConfigureRatioModelLegend(TLegendEntry* leGamma,
                               TLegendEntry* lePositron,
                               TGraph& gammaModel,
                               TGraph& positronModel)
{
	leGamma->SetObject(&gammaModel);
	leGamma->SetLabel("#gamma (best fit model)");
	leGamma->SetOption("L");
	lePositron->SetObject(&positronModel);
	lePositron->SetLabel("e^{+} (best fit model)");
	lePositron->SetOption("L");
	lePositron->SetLineStyle(2);
}

}  // namespace

dybGammaData::dybGammaData()
{
	//cout << " -----> Initializing gamma peaks " << endl;
	//cout << " finished gamma data initialization <------ " << endl;
}
void dybGammaData::AddPeak(string name,string pdfName,double eTruSingle,double eTruTotal)
{
	std::cout << " adding " << name << " peak" << std::endl;
	dybGammaPeak peak(name.c_str(),pdfName.c_str(),eTruSingle,eTruTotal);
	m_data.push_back(peak);
}
void dybGammaData::LoadData(string fileName)
{
	m_data.clear();
	///     --name--        --pdf-- --true E----
	///                              total single
	AddPeak("^{137}Cs"     ,"hECs" ,0.6617,0.6617);
	AddPeak("^{54}Mn"      ,"hEMn" ,0.8348,0.8348);
	AddPeak("^{68}Ge"      ,"hEGe" ,1.022 ,0.511 ); 
	//AddPeak("^{40}K"       ,"hEK"  ,1.4608,1.4608);
	AddPeak("n-H"          ,"hEnH" ,2.2233,2.2233);
	AddPeak("^{60}Co"      ,"hECo" ,2.506 ,1.250 );
	//AddPeak("^{208}Tl"     ,"hETl" ,2.614 ,2.614 );
	//AddPeak("n-^{12}C"     ,"hEnC" ,4.945 ,5.150 );
	AddPeak("n-^{12}C"     ,"hEnC" ,4.95 ,4.95 );
	AddPeak("^{16}O*"      ,"hEO16",6.129 ,6.129 );
	//AddPeak("n-^{56}Fe_{7.63}","hEFe" ,7.637 ,7.637 );
	//AddPeak("n-^{56}Fe_{2}","hEFe" ,7.63  ,7.63  );
	//AddPeak("n-Gd"         ,"hEnGd",8.05  ,2.05  );
	//AddPeak("^{12}C*"      ,"hEC12",4.439 ,4.439 );
	std::cout << " -----> Reading gamma data from " << fileName << std::endl;
	ifstream infile(fileName.c_str());
	double eRec,eRecError,osBias;
	int i=0;
	while (infile >> eRec >> eRecError)
	{
		if(i>=m_data.size())
			std::cout << " ERROR: Data file contains more gamma peaks than initialized" << std::endl;
		m_data[i].SetERec     (eRec);
		m_data[i].SetERecError(eRecError);
		if(m_data[i].GetName()=="^{137}Cs") m_data[i].SetBiasOS(0.0 );
		if(m_data[i].GetName()=="^{54}Mn")  m_data[i].SetBiasOS(0.0 );
		if(m_data[i].GetName()=="^{68}Ge")  m_data[i].SetBiasOS(0.0);
		if(m_data[i].GetName()=="^{40}K")   m_data[i].SetBiasOS(0.0);
		if(m_data[i].GetName()=="^{60}Co")  m_data[i].SetBiasOS(0.0 );
		if(m_data[i].GetName()=="n-H")      m_data[i].SetBiasOS(0.0);
		if(m_data[i].GetName()=="^{16}O")   m_data[i].SetBiasOS(0.0);
		if(m_data[i].GetName()=="n-Gd")     m_data[i].SetBiasOS(0.0 );
		i++;
	}
	if(i!=m_data.size())
		std::cout << " ERROR: Data file contains less gamma peaks than initialized" << std::endl;
}
double dybGammaData::GetChi2(int nDoF)
{
	double chi2 = 0;
	vector<dybGammaPeak>::iterator peakItr = m_data.begin();
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
void dybGammaData::Plot(bool writeToFile)
{
	cout << " ---> Intializing Gamma data " << endl;
	TGraphErrors* peaksScint   = new TGraphErrors;
	TGraphErrors* peaksScintM  = new TGraphErrors;
	TGraphErrors* peaksScintR  = new TGraphErrors;
	TGraphErrors* peaksScintMR = new TGraphErrors;
	TGraphErrors* peaksFullNL  = new TGraphErrors;
	TGraphErrors* peaksFullNLM = new TGraphErrors;
	TGraphErrors* peaksFullNLR  = new TGraphErrors;
	TGraphErrors* peaksFullNLMR = new TGraphErrors;
	TGraphErrors* peaksElec    = new TGraphErrors;
	TGraphErrors* peaksFull    = new TGraphErrors;
	TGraphErrors* peaksFullM   = new TGraphErrors;
	StyleGammaRatioGraph(peaksScint, false);
	StyleGammaRatioGraph(peaksScintR, false);
	StyleGammaRatioGraph(peaksFullNL, false);
	StyleGammaRatioGraph(peaksFullNLR, false);
	StyleGammaRatioGraph(peaksScintM, true);
	StyleGammaRatioGraph(peaksScintMR, true);
	StyleGammaRatioGraph(peaksFullNLM, true);
	StyleGammaRatioGraph(peaksFullNLMR, true);
	peaksFull   ->SetLineColor  (kBlue+1);
	peaksElec   ->SetLineColor  (kBlue+1);
	peaksFull   ->SetMarkerColor(kBlue+1);
	peaksElec   ->SetMarkerColor(kBlue+1);
	peaksFullM  ->SetMarkerColor(kWhite);
	peaksFull   ->SetMarkerStyle(20);
	peaksElec   ->SetMarkerStyle(20);
	peaksFullM  ->SetMarkerStyle(20);
	peaksFull   ->SetMarkerSize(1.1);
	peaksElec   ->SetMarkerSize(1.1);
	peaksFullM  ->SetMarkerSize(0.5);
	vector<dybGammaPeak>::iterator peakItr = m_data.begin();
	TGraph gammaNL = dybEnergyModel::DrawGammaScintNL();
	TGraph gammaFullNL = dybEnergyModel::DrawGammaFullNL();
	int pointIdx    = 0;
	int idxMultiple = 0;
	for(;peakItr!=m_data.end();peakItr++)
	{
		peakItr->UpdateTheoNL();
		peakItr->UpdateDataNL();
		double eEff     = peakItr->GetEffectiveEnergy();
		double error    = peakItr->GetERecError();
		double nlScint  = peakItr->GetDataScintNL();
        double nlScint_theo = gammaNL.Eval(eEff);
		double nlFull   = peakItr->GetDataFullNL();
		double nlFull_theo = gammaFullNL.Eval(eEff);
		double eVis     = peakItr->GetEVis();
		double eRec     = peakItr->GetERec();
		double eTru     = peakItr->GetETruTotal();
		peaksFull  ->SetPoint     (pointIdx,eTru,eRec/eTru);
		peaksFull  ->SetPointError(pointIdx,0,   eRec/eTru*error);
		peaksElec  ->SetPoint     (pointIdx,eVis,eRec/eVis);
		peaksElec  ->SetPointError(pointIdx,0,   eRec/eVis*error);
		peaksScint ->SetPoint     (pointIdx,eEff,nlScint);
		peaksScint ->SetPointError(pointIdx,0,nlScint*error);
		peaksScintR->SetPoint     (pointIdx,eEff,nlScint/nlScint_theo);
		peaksScintR->SetPointError(pointIdx,0,error*nlScint/nlScint_theo);
		peaksFullNL ->SetPoint     (pointIdx,eEff,nlFull);
		peaksFullNL ->SetPointError(pointIdx,0,nlFull*error);
		peaksFullNLR->SetPoint     (pointIdx,eEff,nlFull/nlFull_theo);
		peaksFullNLR->SetPointError(pointIdx,0,error*nlFull/nlFull_theo);
		
		if(!peakItr->IsSingleGamma() || peakItr->GetName()=="n-^{12}C")
		{
			peaksFullM  ->SetPoint     (idxMultiple,eTru,eRec/eTru);
			peaksFullM  ->SetPointError(idxMultiple,0,nlScint*error);
			peaksScintM ->SetPoint     (idxMultiple,eEff,nlScint);
			peaksScintM ->SetPointError(idxMultiple,0,nlScint*error);
			peaksScintMR->SetPoint     (idxMultiple,eEff,nlScint/nlScint_theo);
			peaksScintMR->SetPointError(idxMultiple,0,error*nlScint/nlScint_theo);
			peaksFullNLM ->SetPoint     (idxMultiple,eEff,nlFull);
			peaksFullNLM ->SetPointError(idxMultiple,0,nlFull*error);
			peaksFullNLMR->SetPoint     (idxMultiple,eEff,nlFull/nlFull_theo);
			peaksFullNLMR->SetPointError(idxMultiple,0,error*nlFull/nlFull_theo);
			idxMultiple++;
		} 
		pointIdx++;
	}
	TMultiGraph* allPeaks = new TMultiGraph;
	allPeaks->Add(peaksScint, "PZ");
	allPeaks->Add(peaksScintM,"PZ");
	//TGraph gammaNL = dybEnergyModel::DrawGammaScintNL();
	if(writeToFile)
	{
		TCanvas* tmpC1 = new TCanvas("tmpC1","",700,520);
		TCanvas* tmpC2 = new TCanvas("tmpC2","",700,520);
		TCanvas* tmpC0 = new TCanvas("tmpC0","",700,520);
		tmpC1->cd();
		double chi2 = GetChi2();
		int nPeaks  = m_data.size();
		stringstream ssChi2;ssChi2.precision(3);ssChi2<<chi2;
		stringstream ssPeak;ssPeak<<nPeaks;
		//peaksSingle->SetTitle("Gamma Data;Effective Single gamma energy [MeV];Scintillator Non-linearity");
		TString name = dybParameters::title;
		//TString gamTitle = "Gamma ray data: #chi^{2} = "+ssChi2.str()+" / "+ssPeak.str()+" peaks;Effective Single #gamma Energy [MeV];Scintillator Non-Linearity";
		TString gamTitle = " ;Effective single #gamma energy [MeV];Scintillator nonlinearity";
		//TString gamTitle = "Gamma Data - Scintillator NL: #chi^{2} = "+ssChi2.str()+";Effective Single #gamma Energy [MeV];Scintillator Non-Linearity";
		//TString gamTitle = "Gamma Calibration Data;Effective Single #gamma Energy [MeV];Scintillator Non-Linearity";

                //std::cout<<"^^^^^"<<std::endl;
                dybLSData *lsData_LBNL = new dybLSData("LBNL");
                //std::cout<<"!!!!!!"<<std::endl;
                lsData_LBNL->LoadData(dybParameters::lsData_file_LBNL);
                //std::cout<<"??????"<<std::endl;
                TGraphErrors gr_scint = lsData_LBNL->Plot();
                //std::cout<<"@@@@@@"<<std::endl;
		TGraph positronNL = dybEnergyModel::DrawPositronScintNL();
		TGraph positronFullNL = dybEnergyModel::DrawPositronFullNL();
		peaksScint->SetTitle(gamTitle);
		peaksScint->Draw("APZ");
		gammaNL.SetMarkerStyle(7);
		gammaNL.SetMarkerColor(kRed+1);
		gammaNL.SetLineColor  (kRed+1);
		gammaNL.SetLineWidth(2);
		gammaNL.Draw("C");
                double a,b;
                for(int z=0;z<31;z++)
                  {
                  gr_scint.GetPoint(z,a,b);
                  //std::cout<<"a="<<a<<" b="<<b<<std::endl;
                  }
                //gr_scint.SetFillColor(17);
                //gr_scint.Draw("3");
                //gr_scint.SetLineColor(0);
		peaksScint ->Draw("PZ");
		peaksScintM->Draw("PZ");
		TLegend* leg=new TLegend(0.52,0.1,0.82,0.5);
		leg->SetBorderSize(0);
		leg->SetFillColor(-1);
		TLegendEntry *leS = leg->AddEntry(peaksScint,"Single gamma source","PE");
		TLegendEntry *leM = leg->AddEntry(peaksScint,"Multiple gamma source","PE");
		TLegendEntry *leF = leg->AddEntry(&gammaNL,   " "," ");
		TLegendEntry *leP = leg->AddEntry(&positronNL," "," ");
		leM->SetLineColor  (kBlue+1);
		leS->SetLineColor  (kBlue+1);
		leg->SetTextSize(19);
		leg->Draw();
		TLegend* legB=new TLegend(0.52,0.1,0.82,0.5);
		legB->SetBorderSize(0);
		legB->SetFillStyle(-1);
		legB->SetFillColor(-1);
		TLegendEntry *leSB = legB->AddEntry((TObject*)0," "," ");
		TLegendEntry *leMB = legB->AddEntry(peaksScintM," ","P");
		TLegendEntry *leFB = legB->AddEntry((TObject*)0," "," ");
		TLegendEntry *lePB = legB->AddEntry((TObject*)0," "," ");
		legB->SetTextSize(19);
		legB->Draw();
		float oldSize = gStyle->GetTitleSize("T");
		gStyle->SetTitleSize(0.05,"T");  
		/// raw data
		tmpC0->cd();
		peaksFull->SetTitle("Gamma ray calibration data;Total gamma energy [MeV];Reconstructed energy / true energy");
		peaksFull ->GetYaxis()->SetTitleOffset(1.1);
		peaksFull ->Draw("APZ");
		peaksFullM->Draw("PZ");
		leg ->DrawClone();
		legB->DrawClone();
		leF->SetLabel("Best fit model");
		leF->SetOption("L");
		/// split canvas
		TCanvas* tmpC3 = new TCanvas("tmpC3_gamma_ratio","",700,520);
		TCanvas* tmpC4 = new TCanvas("tmpC4_gamma_ratio_fullNL","",700,520);
		TPad* pad1Ratio = 0;
		ConfigureRatioModelLegend(leF, leP, gammaNL, positronNL);
		DrawGammaRatioCanvas(tmpC3,
		                     peaksScint,
		                     peaksScintM,
		                     peaksScintR,
		                     peaksScintMR,
		                     gammaNL,
		                     positronNL,
		                     leg,
		                     legB,
		                     "Scintillator nonlinearity",
		                     0.825,
		                     1.065,
		                     pad1Ratio);
		TPad* pad1RatioFullNL = 0;
		ConfigureRatioModelLegend(leF, leP, gammaFullNL, positronFullNL);
		DrawGammaRatioCanvas(tmpC4,
		                     peaksFullNL,
		                     peaksFullNLM,
		                     peaksFullNLR,
		                     peaksFullNLMR,
		                     gammaFullNL,
		                     positronFullNL,
		                     leg,
		                     legB,
		                     "Full nonlinearity",
		                     0.825,
		                     1.065,
		                     pad1RatioFullNL);
		
		tmpC2->cd();
		dybFadcData fadcData;
		fadcData.LoadData(dybParameters::fadcData_file);
		TGraphErrors gr = fadcData.Plot();
		stringstream ssChi2Fadc;ssChi2Fadc.precision(3);ssChi2Fadc<<fadcData.GetChi2();
		//TString elecTitle = "Gamma+FADC Data: #chi^{2} = "+ssChi2Fadc.str()+";Visible Energy [MeV];Electronics Non-Linearity";
		TString elecTitle = ";Visible energy [MeV];Electronics nonlinearity";
		peaksElec->SetTitle(elecTitle);
		//peaksElec->SetTitle("Gamma+FADC Data - Electronics NL;Visible Energy [MeV];Electronics Non-Linearity");
		//peaksElec->GetYaxis()->SetRangeUser(0.94,1.08);
		peaksElec->GetYaxis()->SetRangeUser(0.99,1.12);
	 
		//peaksElec->GetYaxis()->SetLimits(0.82,1.1);
		peaksElec->Draw("APZ");
		gr.SetFillColor(17);
		//gr.SetLineColor(kGray+1);
		//gr.SetLineWidth(3);
		//gr.SetTitle("FADC Data NOT Included in Fit;Visible Energy [MeV];Electronics Non-Linearity");
		gr.Draw("3");
		//gr.Draw("LX0");
		gr.SetLineColor(0);
		peaksElec->Draw("PZ");
		TGraph electronicsNL = dybEnergyModel::DrawElectronicsNL();
		electronicsNL.SetMarkerStyle(7);
		electronicsNL.SetMarkerColor(kRed+1);
		electronicsNL.SetLineColor(kRed+1);
		electronicsNL.SetLineWidth(2);
		electronicsNL.Draw("C");
		TLegend* leg2=new TLegend(0.68,0.65,0.88,0.88);
		leg2->SetBorderSize(0);
		leg2->SetFillColor(0);
		TLegendEntry *le2S = leg2->AddEntry(peaksElec,"Gamma data","PE");
		leg2->AddEntry(&gr,"FADC data","F");
		leg2->AddEntry(&electronicsNL,"Best fit model","L");
		leg2->SetTextSize(19);
		leg2->Draw();
		for(peakItr = m_data.begin();peakItr!=m_data.end();peakItr++)
		{
			TLatex latex;
			double eEff    = peakItr->GetEffectiveEnergy();
			double eVis    = peakItr->GetEVis();
			double eTru    = peakItr->GetETruTotal();
			double nlFull  = peakItr->GetDataFullNL();
			double nlScint = peakItr->GetDataScintNL();
			double nlElec  = peakItr->GetERec()/peakItr->GetEVis();
			string name    = peakItr->GetName();
			latex.SetTextSize(0.035);
			latex.SetTextColor(kBlue+2);
			if(peakItr->IsSingleGamma())
			{
				latex.SetTextAlign(13);  //align at top left
				tmpC1->cd();
				latex.DrawLatex(eEff+0.08,nlScint-0.006,name.c_str());
				tmpC0->cd();
				if(eTru<2.0)
					latex.DrawLatex(eTru+0.1,nlFull-0.01,name.c_str());
				else if(eTru<2.3)
					latex.DrawLatex(eTru+0.0,nlFull-0.009,name.c_str());
				else
					latex.DrawLatex(eTru+0.1,nlFull+0.01,name.c_str());
				tmpC3->cd();
				pad1Ratio->cd();
				latex.SetTextSize(0.045);
				if(eEff<0.7) latex.DrawLatex(eEff-0.4,nlScint+0.02,name.c_str());
				if(eEff>0.7) latex.DrawLatex(eEff-0.2,nlScint+0.02,name.c_str());
				//latex.DrawLatex(eEff+0.08,nlScint-0.008,name.c_str());
				tmpC4->cd();
				pad1RatioFullNL->cd();
				latex.SetTextSize(0.045);
				if(eEff<0.7) latex.DrawLatex(eEff-0.4,nlFull+0.02,name.c_str());
				if(eEff>0.7) latex.DrawLatex(eEff-0.2,nlFull+0.02,name.c_str());
				latex.SetTextSize(0.035);
				latex.SetTextAlign(23); 
				tmpC2->cd();
				//latex.DrawLatex(eVis+0.08,nlElec-0.012,name.c_str());
				//if(eVis<0.7) latex.DrawLatex(eVis-0.1,nlElec-0.01,name.c_str());
                                //else if(eVis<0.83) latex.DrawLatex(eVis,nlElec+0.005,name.c_str());
                                //else if(eVis<1.1) latex.DrawLatex(eVis,nlElec-0.006,name.c_str());
                                //else if(eVis<2.4) latex.DrawLatex(eVis-0.2,nlElec-0.01,name.c_str());
				//else if(eVis<2.8) latex.DrawLatex(eVis,nlElec-0.01,name.c_str());
                                //else if(eVis<3) latex.DrawLatex(eVis,nlElec+0.015,name.c_str());
                                //else if(eVis<7) latex.DrawLatex(eVis+0.05,nlElec-0.012,name.c_str());
                                //else if(eVis<9) latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
                                //else latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
				//cout<<name.c_str()<<" "<<"eVis="<<eVis<<endl;
				if(eVis<0.7) latex.DrawLatex(eVis-0.1,nlElec+0.015,name.c_str());
                                else if(eVis<0.83) latex.DrawLatex(eVis+0.35,nlElec+0.005,name.c_str());
                                else if(eVis<1.1) latex.DrawLatex(eVis,nlElec-0.012,name.c_str());
                                else if(eVis<1.6) latex.DrawLatex(eVis,nlElec-0.012,name.c_str());
                                else if(eVis<2.4) latex.DrawLatex(eVis-0.1,nlElec+0.01,name.c_str());
                                else if(eVis<2.6) latex.DrawLatex(eVis-0.4,nlElec-0.01,name.c_str());
                                else if(eVis<3) latex.DrawLatex(eVis+0.02,nlElec+0.012,name.c_str());
                                else if(eVis<7) latex.DrawLatex(eVis+0.05,nlElec-0.012,name.c_str());
                                else if(eVis<9) latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
                                else latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
			}
			else
			{
				latex.SetTextAlign(31);  //align at bottom right
				tmpC0->cd();
				latex.DrawLatex(eTru+0.,nlFull-0.005,name.c_str());
				tmpC1->cd();
				if(eEff>0.7)latex.DrawLatex(eEff-0.08,nlScint+0.007,name.c_str());
				if(eEff<0.7) latex.DrawLatex(eTru+0.13,nlScint-0.006,name.c_str());
				tmpC3->cd();
				pad1Ratio->cd();
				latex.SetTextSize(0.045);
				if(eEff<0.7) latex.DrawLatex(eTru+0.008,nlScint-0.02,name.c_str());
				if(eEff>0.7) latex.DrawLatex(eEff-0.08,nlScint+0.006,name.c_str());
				tmpC4->cd();
				pad1RatioFullNL->cd();
				latex.SetTextSize(0.045);
				if(eEff<0.7) latex.DrawLatex(eTru+0.008,nlFull-0.02,name.c_str());
				if(eEff>0.7) latex.DrawLatex(eEff-0.08,nlFull+0.006,name.c_str());
				//if(eEff<0.7) latex.DrawLatex(eTru+0.11,nlScint-0.006,name.c_str());
				//if(eEff>0.7) latex.DrawLatex(eEff-0.08,nlScint+0.006,name.c_str());
				latex.SetTextSize(0.035);
				tmpC2->cd();
				latex.SetTextAlign(21);
				//latex.DrawLatex(eVis,nlElec+0.012,name.c_str());
				//if(eVis<0.7) latex.DrawLatex(eVis-0.1,nlElec-0.01,name.c_str());
                                //else if(eVis<0.83) latex.DrawLatex(eVis,nlElec+0.005,name.c_str());
                                //else if(eVis<1.1) latex.DrawLatex(eVis,nlElec-0.006,name.c_str());
                                //else if(eVis<2.4) latex.DrawLatex(eVis-0.2,nlElec-0.01,name.c_str());
                                //else if(eVis<2.8) latex.DrawLatex(eVis,nlElec-0.01,name.c_str());
                                //else if(eVis<3) latex.DrawLatex(eVis,nlElec+0.015,name.c_str());
                                //else if(eVis<7) latex.DrawLatex(eVis+0.05,nlElec-0.012,name.c_str());
                                //else if(eVis<9) latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
                                //else latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
				//cout<<"$$$$$$$$$$$"<<endl;
				//cout<<name.c_str()<<" "<<"eVis="<<eVis<<endl;
				if(eVis<0.7) latex.DrawLatex(eVis-0.1,nlElec-0.01,name.c_str());
                                else if(eVis<0.83) latex.DrawLatex(eVis,nlElec+0.005,name.c_str());
                                else if(eVis<1.1) latex.DrawLatex(eVis,nlElec-0.012,name.c_str());
                                else if(eVis<2.4) latex.DrawLatex(eVis-0.2,nlElec-0.01,name.c_str());
                                else if(eVis<2.8) latex.DrawLatex(eVis,nlElec-0.01,name.c_str());
                                else if(eVis<3) latex.DrawLatex(eVis,nlElec+0.015,name.c_str());
                                else if(eVis<6) latex.DrawLatex(eVis+0.05,nlElec+0.012,name.c_str());
                                else if(eVis<7) latex.DrawLatex(eVis+0.05,nlElec-0.012,name.c_str());
                                else if(eVis<9) latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
                                else latex.DrawLatex(eVis-0.25,nlElec+0.02,name.c_str());
			}
		}
		string plotName = dybParameters::plotFolder+dybParameters::toyKey+"_gamma."+dybParameters::plotFormat;
		tmpC1->SaveAs(plotName.c_str());
		plotName = dybParameters::plotFolder+dybParameters::toyKey+"_gamma2."+dybParameters::plotFormat;
		tmpC2->SaveAs(plotName.c_str());
		plotName = dybParameters::plotFolder+dybParameters::toyKey+"_gamma_ratio."+dybParameters::plotFormat;
		tmpC3->SaveAs(plotName.c_str());
		plotName = dybParameters::plotFolder+dybParameters::toyKey+"_gamma_ratio_fullNL."+dybParameters::plotFormat;
		tmpC4->SaveAs(plotName.c_str());
		plotName = dybParameters::plotFolder+dybParameters::toyKey+"_gamma_raw."+dybParameters::plotFormat;
		tmpC0->SaveAs(plotName.c_str());
		delete tmpC1;
		delete tmpC2;
		delete tmpC3;
		delete tmpC4;
		delete tmpC0;
		string outname = "output/gammas/gammas_"+dybParameters::toyKey+".root";
		TFile* gammaFile = new TFile(outname.c_str(),"recreate");
		peaksScint  ->Write("peaksSingle")   ;
		peaksScintM ->Write("peaksScintM") ;
		peaksScintR ->Write("peaksScintR")  ;
		peaksScintMR->Write("peaksScintMR");
		peaksElec   ->Write("peaksElec")     ;
		peaksFull   ->Write("peaksFull")     ;
		gammaFile->Close();
		delete gammaFile;
	}
}
TGraphErrors dybGammaData::PlotPeaks(int type)
{
	cout << " ---> Intializing Gamma data " << endl;
	TGraphErrors gr(0);
	gr.SetLineColor  (kBlue+2);
	gr.SetMarkerColor(kBlue+2);
	gr.SetMarkerStyle(10);
	gr.SetMarkerSize (0.6);
	vector<dybGammaPeak>::iterator peakItr = m_data.begin();
	int pointIdx=0;
	for(;peakItr!=m_data.end();peakItr++)
	{
		std::cout << peakItr->GetName() << std::endl;
		//std::cout << peakItr->GetETruSingle() << std::endl;
		//std::cout << peakItr->GetERec() << std::endl;
		double energy   = peakItr->GetETruSingle();
		double error    = peakItr->GetERecError();
		double nl       = 1;
		peakItr->UpdateDataNL();
		if(type==1) nl = peakItr->GetDataScintNL();
		if(type==2) nl = peakItr->GetDataFullNL ();
		if(type==3) nl = peakItr->GetTheoScintNL();
		if(type==4) nl = peakItr->GetTheoFullNL ();
		//std::cout << " nl = " << nl << std::endl;
		//std::cout << " error = " << error << std::endl;
		gr.SetPoint     (pointIdx,energy,nl);
		gr.SetPointError(pointIdx,0,nl*error);
		pointIdx++;
	}
	return gr;
}
void dybGammaData::GenToyMC()
{
	std::cout << " ------> Generating " << dybParameters::nToy << " gamma toy MC samples " << std::endl;
	TRandom3 rand;
	for (int toyIdx=0; toyIdx<dybParameters::nToy; toyIdx++)
	{
		stringstream ss; ss<<toyIdx;
		std::string toyName = dybParameters::toyFolder;
		toyName += "gammaToy_" + dybParameters::toyKey + "_" +  ss.str() + ".dat";
		ofstream toyFile(toyName.c_str());
		vector<dybGammaPeak>::iterator peakItr = m_data.begin();
		for(;peakItr!=m_data.end();peakItr++)
		{
			peakItr->UpdateTheoNL();
			double eRec      = peakItr->GetTheoFullNL() * peakItr->GetETruTotal();
			double eRecError = peakItr->GetERecError  ();
			double toyERec   = rand.Gaus(eRec,eRec*eRecError);
			toyFile << toyERec << " " << eRecError << endl;
		}
		toyFile.close();
	}
}
