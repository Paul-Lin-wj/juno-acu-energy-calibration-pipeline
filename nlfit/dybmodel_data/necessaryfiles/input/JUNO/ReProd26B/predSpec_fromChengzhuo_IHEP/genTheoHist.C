const TString tag="P25C";
/*
const int Nbr = 1;
const double m_BR[Nbr] = {1}; 
const int m_numPhoton[Nbr] = {0}; 
const double m_photonE[Nbr][10] = {{}}; 
const TString iso="C11";
//const TString findata="11C_P25B_By_ChengzhuoIHEP.root";
//const TString foutdata="C11_P25B.root";
const TString findata= tag + "/OMILREC_11C_P25CminiAEDM_ECorr_By_Chengzhuo.root";
const TString histname="FV/hE_diff_FV";

const int Nbr = 2;
const double m_BR[Nbr] = {0.985354, 0.014646}; 
const int m_numPhoton[Nbr] = {1,2}; 
const double m_photonE[Nbr][10] = {{0.71833},{1.02165,0.71833}}; 
const TString iso="C10";
//const TString findata="10C_P25B_By_ChengzhuoIHEP.root";
//const TString foutdata="C10_P25B.root";
const TString findata= tag + "/OMILREC_10C_P25CminiAEDM_ECorr_By_Chengzhuo.root";
const TString histname="FV/hE_diff_FV";
*/


const TString iso="B12";
const TString findata= tag + "/OMILREC_12B_P25CminiAEDM_ECorr_By_Chengzhuo.root";
const TString histname="First_in(6-90ms)_off(90-174ms)/FV/hE_diff_First_FV";


const int rebin=5;
const TString foutdata= tag+"/"+iso+"_data.root";
void genTheoHist(){
    TFile *fin, *fout;
/*
    const TString foutname= iso + "_hist.root";
    const TString finname = iso + "_pred.root";
    fin = TFile::Open(finname.Data(),"READ"); 
    TH1F* hh[Nbr];
    TH1D* temp;
    int Nbins=0;
    for(int ibr=0; ibr<Nbr; ibr++){
        temp = (TH1D*) fin->Get(Form("%s_betaSpec_%i",iso.Data(),ibr+1));
        Nbins = temp->GetNbinsX();
        hh[ibr] = new TH1F(Form("hh%i",ibr),Form("hh%i",ibr),Nbins,temp->GetXaxis()->GetBinLowEdge(1),temp->GetXaxis()->GetBinLowEdge(Nbins+1));
        for(int bin=1; bin<=Nbins; bin++){ 
            hh[ibr]->SetBinContent(bin,temp->GetBinContent(bin));
        }
        hh[ibr]->SetDirectory(0);
    }
    fin->Close();

    int num, numPhoton;
    double BR, photonE[10]={};
    TTree* tree = new TTree("T","T");
    tree->Branch("num",&num,"num/I");
    tree->Branch("BR", &BR, "BR/D");
    tree->Branch("numPhoton",&numPhoton,"numPhoton/I");
    tree->Branch("photonE",  photonE,  "photonE[numPhoton]/D");

    for(int ibr=0; ibr<Nbr; ibr++){
        num= ibr;
        BR = m_BR[ibr];
        numPhoton = m_numPhoton[ibr];
        for(int i=0; i<numPhoton; i++)
            photonE[i] = m_photonE[ibr][i];
        tree->Fill();
    }

    fout = new TFile(foutname.Data(),"RECREATE");
    for(int ibr=0; ibr<Nbr; ibr++)
            hh[ibr]->Write();
    tree->Write();
    fout->Close();
*/

    fin = TFile::Open(findata.Data(),"READ");
    TH1D* h_iso = (TH1D*) fin->Get(histname.Data());
    if(h_iso) cout<<"Find "<<histname<<endl;
    h_iso->Rebin(rebin);
    //h_iso->SetDirectory(0);
    fout = new TFile(foutdata.Data(),"RECREATE");
    h_iso->Write(Form("%s_data",iso.Data()));
    //h_iso->Write();
    fout->Close();
    fin->Close();
}
