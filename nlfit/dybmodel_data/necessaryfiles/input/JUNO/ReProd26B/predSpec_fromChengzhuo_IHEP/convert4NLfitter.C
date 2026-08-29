/////////////////////////////////////////////////////////////////////////////////////////////
// Enter dybOS6 (SL6) container first, then cd to this directory.
// If input ROOT was produced on el9/modern ROOT, export sidecars on el9 first:
//   root -l -b -q 'export_predSpec_sidecar.C("12B_pure_beta_0_20MeV_80bins.root")'
// Or run the full pipeline:
//   bash run_convert_sl6.sh
// Then in SL6:
//   root -l -b -q 'convert4NLfitter.C("12B_pure_beta_0_20MeV_80bins.root")'
/////////////////////////////////////////////////////////////////////////////////////////////

#include "TFile.h"
#include "TH1F.h"
#include "TROOT.h"
#include "TString.h"
#include "TSystem.h"
#include "TTree.h"
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

bool Is11BePredSpec(const char* fname)
{
    const char* base = gSystem->BaseName(fname);
    return std::strstr(base, "11Be_") != 0;
}

void RenumberTreeNumsFor11Be(std::vector<int>& nums, size_t nHist)
{
    if (nums.size() != nHist) {
        std::cerr << "WARNING: 11Be tree entries (" << nums.size()
                  << ") != histogram count (" << nHist << ")" << std::endl;
    }
    const size_t n = nums.size() < nHist ? nums.size() : nHist;
    for (size_t i = 0; i < n; ++i) {
        nums[i] = int(i);
    }
}


bool LoadTreeFromSidecar(const char* fname, std::vector<int>& nums, std::vector<double>& brs,
                         std::vector<int>& numPhotons, std::vector<std::vector<double> >& photonEs)
{
    TString sidecar = Form("sidecar/%s.tree", gSystem->BaseName(fname));
    if (gSystem->AccessPathName(sidecar)) {
        return false;
    }

    std::ifstream in(sidecar.Data());
    if (!in) {
        std::cerr << "ERROR: cannot open " << sidecar << std::endl;
        return false;
    }

    std::string tag;
    long long nEntries = 0;
    in >> tag >> nEntries;
    if (tag != "ENTRIES") {
        std::cerr << "ERROR: malformed tree sidecar" << std::endl;
        return false;
    }

    nums.clear();
    brs.clear();
    numPhotons.clear();
    photonEs.clear();
    for (long long i = 0; i < nEntries; ++i) {
        std::string line;
        in >> tag;
        if (tag != "BRANCH") {
            std::cerr << "ERROR: expected BRANCH in tree sidecar" << std::endl;
            return false;
        }
        int num = 0;
        int numPhoton = 0;
        double br = 0.0;
        in >> num >> br >> numPhoton;
        std::vector<double> gam;
        for (int ig = 0; ig < numPhoton; ++ig) {
            double e = 0.0;
            in >> e;
            gam.push_back(e);
        }
        nums.push_back(num);
        brs.push_back(br);
        numPhotons.push_back(numPhoton);
        photonEs.push_back(gam);
    }
    in >> tag;
    if (tag != "ENDTREE") {
        std::cerr << "ERROR: expected ENDTREE in tree sidecar" << std::endl;
        return false;
    }
    return !nums.empty();
}

bool ReadTreeFromInput(TFile* fin, std::vector<int>& nums, std::vector<double>& brs,
                       std::vector<int>& numPhotons, std::vector<std::vector<double> >& photonEs)
{
    TTree* tin = (TTree*)fin->Get("T");
    if (!tin) {
        std::cerr << "ERROR: missing TTree T in input file" << std::endl;
        return false;
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
    nums.clear();
    brs.clear();
    numPhotons.clear();
    photonEs.clear();
    for (Long64_t ibr = 0; ibr < nbr; ++ibr) {
        tin->GetEntry(ibr);
        nums.push_back(m_num);
        brs.push_back(m_BR);
        numPhotons.push_back(m_numPhoton);
        std::vector<double> gam;
        if (m_photonE) {
            for (int ig = 0; ig < m_numPhoton; ++ig) {
                gam.push_back((*m_photonE)[ig]);
            }
        }
        photonEs.push_back(gam);
    }
    return true;
}

bool LoadHistFromSidecar(const char* fname, std::vector<TH1F*>& hists)
{
    TString sidecar = Form("sidecar/%s.hist", gSystem->BaseName(fname));
    if (gSystem->AccessPathName(sidecar)) {
        return false;
    }

    std::ifstream in(sidecar.Data());
    if (!in) {
        std::cerr << "ERROR: cannot open sidecar " << sidecar << std::endl;
        return false;
    }

    std::string tag;
    while (in >> tag) {
        if (tag != "HIST") {
            std::cerr << "ERROR: malformed sidecar near tag " << tag << std::endl;
            return false;
        }
        std::string name;
        int nbins = 0;
        double xmin = 0.0;
        double xmax = 0.0;
        in >> name >> nbins >> xmin >> xmax;
        TH1F* hist = new TH1F(name.c_str(), name.c_str(), nbins, xmin, xmax);
        for (int ib = 1; ib <= nbins; ++ib) {
            int bin = 0;
            double content = 0.0;
            double error = 0.0;
            in >> bin >> content >> error;
            hist->SetBinContent(bin, content);
            hist->SetBinError(bin, error);
        }
        std::string endTag;
        in >> endTag;
        if (endTag != "ENDHIST") {
            std::cerr << "ERROR: expected ENDHIST after " << name << std::endl;
            delete hist;
            return false;
        }
        hists.push_back(hist);
    }
    return !hists.empty();
}

bool LoadHistFromInput(TFile* fin, int nbr, std::vector<TH1F*>& hists)
{
    for (int ibr = 0; ibr < nbr; ++ibr) {
        TH1F* htemp = (TH1F*)fin->Get(Form("hh%d", ibr));
        if (!htemp) {
            return false;
        }
        TH1F* hcopy = (TH1F*)htemp->Clone(Form("hh%d", ibr));
        hcopy->SetDirectory(0);
        hists.push_back(hcopy);
    }
    return !hists.empty();
}

void WriteOutput(const char* fname, const std::vector<int>& nums, const std::vector<double>& brs,
                 const std::vector<int>& numPhotons, const std::vector<std::vector<double> >& photonEs,
                 const std::vector<TH1F*>& hists)
{
    gSystem->mkdir("forNLfitter", kTRUE);
    TString outName = Form("forNLfitter/%s", gSystem->BaseName(fname));
    TFile* fout = TFile::Open(outName, "RECREATE");
    if (!fout || fout->IsZombie()) {
        std::cerr << "ERROR: cannot create " << outName << std::endl;
        return;
    }

    int num = 0;
    int numPhoton = 0;
    double BR = 0.0;
    std::vector<double> photonE;
    TTree* tree = new TTree("T", "T");
    tree->Branch("num", &num, "num/I");
    tree->Branch("BR", &BR, "BR/D");
    tree->Branch("numPhoton", &numPhoton, "numPhoton/I");
    tree->Branch("photonE", &photonE);

    for (size_t i = 0; i < nums.size(); ++i) {
        num = nums[i];
        BR = brs[i];
        numPhoton = numPhotons[i];
        photonE = photonEs[i];
        tree->Fill();
    }

    for (size_t i = 0; i < hists.size(); ++i) {
        hists[i]->Write(hists[i]->GetName());
    }
    tree->Write();
    fout->Write();
    fout->Close();
    delete fout;
    std::cout << "Wrote " << outName << " with " << hists.size() << " histogram(s) and "
              << nums.size() << " tree entries" << std::endl;
}

} // namespace

void convert4NLfitter(const char* fname = "12B_pure_beta_0_20MeV_80bins.root")
{
    std::vector<int> nums;
    std::vector<double> brs;
    std::vector<int> numPhotons;
    std::vector<std::vector<double> > photonEs;
    std::vector<TH1F*> hists;

    if (LoadTreeFromSidecar(fname, nums, brs, numPhotons, photonEs)) {
        std::cout << "Loaded tree from sidecar/" << gSystem->BaseName(fname) << ".tree" << std::endl;
    } else {
        TFile* fin = TFile::Open(fname, "READ");
        if (!fin || fin->IsZombie()) {
            std::cerr << "ERROR: cannot open input file " << fname << std::endl;
            return;
        }
        if (!ReadTreeFromInput(fin, nums, brs, numPhotons, photonEs)) {
            fin->Close();
            delete fin;
            return;
        }
        gROOT->GetListOfFiles()->Remove(fin);
        fin->Close();
        delete fin;
        std::cout << "Loaded tree directly from input ROOT" << std::endl;
    }

    if (!LoadHistFromSidecar(fname, hists)) {
        TFile* fin = TFile::Open(fname, "READ");
        if (!fin || fin->IsZombie() || !LoadHistFromInput(fin, int(nums.size()), hists)) {
            std::cerr << "ERROR: cannot read hh* for " << fname << std::endl;
            std::cerr << "       Run export_predSpec_sidecar.C on el9 first:" << std::endl;
            std::cerr << "       root -l -b -q 'export_predSpec_sidecar.C(\"" << fname << "\")'"
                      << std::endl;
            if (fin) {
                fin->Close();
                delete fin;
            }
            return;
        }
        gROOT->GetListOfFiles()->Remove(fin);
        fin->Close();
        delete fin;
        std::cout << "Loaded histograms directly from input ROOT" << std::endl;
    } else {
        std::cout << "Loaded histograms from sidecar/" << gSystem->BaseName(fname) << ".hist"
                  << std::endl;
    }

    if (Is11BePredSpec(fname)) {
        RenumberTreeNumsFor11Be(nums, hists.size());
        std::cout << "Renumbered 11Be tree num to match hh0..hh" << (hists.size() - 1)
                  << std::endl;
    }

    WriteOutput(fname, nums, brs, numPhotons, photonEs, hists);
    for (size_t i = 0; i < hists.size(); ++i) {
        delete hists[i];
    }
    gSystem->Exit(0);
}
