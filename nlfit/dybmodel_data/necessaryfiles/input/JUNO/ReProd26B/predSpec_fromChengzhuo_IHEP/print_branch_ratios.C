// Print file-internal normalized BR from predSpec ROOT files.
// Usage: root -l -b -q 'print_branch_ratios.C'

void print_branch_ratios(){
    const char* files[] = {
        "12B_pure_beta_0_20MeV_80bins.root",
        "12N_pure_beta_0_20MeV_80bins.root",
        "10C_pure_beta_0_4MeV_80bins.root",
        "11C_pure_beta_0_4MeV_80bins.root",
        "11Be_pure_beta_0_4MeV_80bins.root",
        "11C_pure_beta_0_4MeV_200bins.root",
    };
    for(const char* fname : files){
        TFile f(fname, "READ");
        TTree* t = (TTree*)f.Get("T");
        if(!t){
            printf("%s: missing TTree T\n", fname);
            continue;
        }
        double br = 0.0;
        t->SetBranchAddress("BR", &br);
        double sum = 0.0;
        printf("%s:\n", fname);
        for(Long64_t i = 0; i < t->GetEntries(); ++i){
            t->GetEntry(i);
            sum += br;
            printf("  raw BR[%lld] = %.6f\n", (long long)i, br);
        }
        if(sum <= 0.0) sum = 1.0;
        for(Long64_t i = 0; i < t->GetEntries(); ++i){
            t->GetEntry(i);
            printf("  norm BR[%lld] = %.6f\n", (long long)i, br / sum);
        }
        printf("  sum(raw) = %.6f\n\n", sum);
    }
}
