void test_theo_read(const char* fname = "forNLfitter/12B_pure_beta_0_20MeV_80bins.root")
{
    TFile* file = TFile::Open(fname, "READ");
    if (!file || file->IsZombie()) {
        cout << "ERROR: cannot open " << fname << endl;
        return;
    }
    TTree* tree = (TTree*)file->Get("T");
    int branchNumber = 0, nGamma = 0;
    double branchRatio = 0.0;
    std::vector<double>* photonEV = 0;
    tree->SetBranchAddress("num", &branchNumber);
    tree->SetBranchAddress("BR", &branchRatio);
    tree->SetBranchAddress("numPhoton", &nGamma);
    tree->SetBranchAddress("photonE", &photonEV);
    for (Long64_t i = 0; i < tree->GetEntries(); ++i) {
        tree->GetEntry(i);
        TH1F* h = (TH1F*)file->Get(Form("hh%d", branchNumber));
        cout << "br=" << branchNumber << " BR=" << branchRatio
             << " bins=" << (h ? h->GetNbinsX() : -1)
             << " int=" << (h ? h->Integral() : -1) << endl;
    }
    file->Close();
    delete file;
    cout << "read ok" << endl;
}
