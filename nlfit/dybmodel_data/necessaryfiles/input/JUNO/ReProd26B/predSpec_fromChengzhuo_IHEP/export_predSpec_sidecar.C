/////////////////////////////////////////////////////////////////////////////////////////////
// Run on el9 login node (modern ROOT) before convert4NLfitter in SL6.
// Writes sidecar/<basename>.hist and sidecar/<basename>.tree
// Usage:
//   root -l -b -q 'export_predSpec_sidecar.C("12B_pure_beta_0_20MeV_80bins.root")'
/////////////////////////////////////////////////////////////////////////////////////////////

#include "TFile.h"
#include "TH1.h"
#include "TKey.h"
#include "TString.h"
#include "TSystem.h"
#include "TTree.h"
#include <fstream>
#include <iostream>
#include <vector>

void export_predSpec_sidecar(const char* fname = "12B_pure_beta_0_20MeV_80bins.root")
{
    gSystem->mkdir("sidecar", kTRUE);

    TFile* fin = TFile::Open(fname, "READ");
    if (!fin || fin->IsZombie()) {
        std::cerr << "ERROR: cannot open " << fname << std::endl;
        return;
    }

    const char* baseName = gSystem->BaseName(fname);
    TString histName = Form("sidecar/%s.hist", baseName);
    TString treeName = Form("sidecar/%s.tree", baseName);
    std::ofstream histOut(histName.Data());
    std::ofstream treeOut(treeName.Data());
    if (!histOut || !treeOut) {
        std::cerr << "ERROR: cannot write sidecar files for " << fname << std::endl;
        fin->Close();
        delete fin;
        return;
    }

    TTree* tin = (TTree*)fin->Get("T");
    if (!tin) {
        std::cerr << "ERROR: missing TTree T in " << fname << std::endl;
        fin->Close();
        delete fin;
        return;
    }

    int m_num = 0;
    int m_numPhoton = 0;
    double m_BR = 0.0;
    std::vector<double>* m_photonE = 0;
    tin->SetBranchAddress("num", &m_num);
    tin->SetBranchAddress("BR", &m_BR);
    tin->SetBranchAddress("numPhoton", &m_numPhoton);
    tin->SetBranchAddress("photonE", &m_photonE);

    const Long64_t nbr = tin->GetEntries();
    treeOut << "ENTRIES " << nbr << "\n";
    for (Long64_t ibr = 0; ibr < nbr; ++ibr) {
        tin->GetEntry(ibr);
        treeOut << "BRANCH " << m_num << " " << m_BR << " " << m_numPhoton;
        if (m_photonE) {
            for (int ig = 0; ig < m_numPhoton; ++ig) {
                treeOut << " " << (*m_photonE)[ig];
            }
        }
        treeOut << "\n";
    }
    treeOut << "ENDTREE\n";

    int nHist = 0;
    TIter next(fin->GetListOfKeys());
    TKey* key = 0;
    while ((key = (TKey*)next())) {
        TObject* obj = key->ReadObj();
        if (!obj) continue;
        TH1* hist = dynamic_cast<TH1*>(obj);
        if (!hist) {
            delete obj;
            continue;
        }
        hist->SetDirectory(0);
        histOut << "HIST " << hist->GetName() << " " << hist->GetNbinsX() << " "
                << hist->GetXaxis()->GetXmin() << " " << hist->GetXaxis()->GetXmax() << "\n";
        for (int ib = 1; ib <= hist->GetNbinsX(); ++ib) {
            histOut << ib << " " << hist->GetBinContent(ib) << " " << hist->GetBinError(ib) << "\n";
        }
        histOut << "ENDHIST\n";
        delete hist;
        ++nHist;
    }

    histOut.close();
    treeOut.close();
    fin->Close();
    delete fin;
    std::cout << "Wrote " << nHist << " histogram(s) to " << histName
              << " and tree to " << treeName << std::endl;
}
