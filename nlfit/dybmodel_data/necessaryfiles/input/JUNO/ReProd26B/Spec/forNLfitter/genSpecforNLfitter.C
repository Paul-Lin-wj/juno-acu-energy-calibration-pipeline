/////////////////////////////////////////////////////////////////////////////////////////////
//  Enter dybOS6 container first
//  Command:
//  root -l -q 'genSpecforNLfitter.C(1,1650,1720)'
/////////////////////////////////////////////////////////////////////////////////////////////

#include "TFile.h"
#include "TH1D.h"
#include "TString.h"
#include "TSystem.h"

const int Nphase=4;
const int Niso = 3;
const TString hname[Niso] = {"B12_data","C11_data","C10_data_pair"};
void genSpecforNLfitter(int phase = 1, int Rcutlow = 0, int Rcuthigh = 1000){
    TString foutname, finname;
    TFile *fin, *fout;
    TH1D* h[Niso];

        foutname = Form("Isotope_data_Phase%d_FVcutR%d_%d.root",phase,Rcutlow,Rcuthigh);
        finname = "../"+foutname;

        fin = TFile::Open(finname.Data(),"READ");
        for(int i=0; i<Niso; i++){
            h[i] = (TH1D*) fin->Get(hname[i].Data());
            h[i]->SetDirectory(0);
        }

        fout = new TFile(foutname.Data(),"RECREATE");
        for(int i=0; i<Niso; i++){
            h[i]->Write(hname[i].Data());
            h[i]->SetDirectory(0);
        }
        fout->Close();
        fin->Close();
}
