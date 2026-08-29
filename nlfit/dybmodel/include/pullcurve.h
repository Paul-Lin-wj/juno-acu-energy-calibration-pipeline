#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <time.h>
#include "TFile.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TH2F.h"
#include "THStack.h"
#include "TMath.h"
#include "TF1.h"
#include "TStyle.h"
#include "TMinuit.h"
#include "TLegend.h"
#include "TApplication.h"
#include "TLegendEntry.h"
#include "TString.h"
#include "TGraph.h"
#include "TTree.h"
#include "TBranch.h"
#include "TGraph2D.h"
#include "TMultiGraph.h"
#include "TRandom3.h"
#include "TGraphErrors.h"
#include "TGraphAsymmErrors.h"
#include "TProfile.h"
#include "TROOT.h"

#include "dybParameters.h"
#include "dybEnergyModel.h"
#include "dybGammaPeak.h"
#include "dybGlobalFit.h"
#include "dybSpectrum.h"
#include "dybBi212Data.h"
#include "dybBi214Data.h"
#include "dybTl208Data.h"
#include "dybLSData.h"
#include "dybGlobalFit.h"
#include "dybMichelData.h"

using namespace std;

void ReadArguments(int argc, char** argv);

void SetStyle()
{
	TStyle *style = new TStyle("Modern","Modern Style");
	style->SetTitleFont(43,"xyz");
	style->SetLabelFont(43,"xyz");
	style->SetLegendFont(43);
	style->SetLabelSize(19,"xyz");
	style->SetTitleSize(21,"xyz");
	style->SetLegendBorderSize(0);
	style->SetLegendFillColor(kRed);
	style->SetStatStyle(0);
	style->SetLineColor(kBlue+1);
	style->SetMarkerStyle(20);
	gROOT->SetStyle("Modern"); 
}
