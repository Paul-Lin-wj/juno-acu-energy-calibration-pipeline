void test_read_forNL(const char* fname = "forNLfitter/sl6_12B_pure_beta_0_20MeV_80bins.root")
{
    TFile f(fname, "READ");
    if (f.IsZombie()) {
        cout << "ERROR: cannot open " << fname << endl;
        return;
    }
    f.ls();
    TH1F* h0 = (TH1F*)f.Get("hh0");
    cout << "hh0 bins=" << (h0 ? h0->GetNbinsX() : -1) << endl;
    if (h0) cout << "hh0 integral=" << h0->Integral() << endl;
    TTree* t = (TTree*)f.Get("T");
    cout << "T entries=" << (t ? t->GetEntries() : -1) << endl;
}
