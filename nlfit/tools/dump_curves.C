// dump_curves.C — write the NL curves from curves_<toyKey>.root to a
// block-format TSV consumable by pure Python (Stage 7):
//
//   # curve <name>
//   <E_true>  <NL>
//   ...
//
// Usage: root -b -q 'dump_curves.C("<in.root>","<out.tsv>")'
#include <fstream>
#include <iomanip>

void dump_curves(const char* inFile, const char* outFile) {
    TFile f(inFile);
    if (f.IsZombie()) {
        std::cerr << "cannot open " << inFile << std::endl;
        gSystem->Exit(1);
    }
    const char* names[] = {
        "electronicsNL", "electronScintNL", "positronScintNL",
        "gammaScintNL", "alphaScintNL",
        "electronFullNL", "positronFullNL", "gammaFullNL", "alphaFullNL"
    };
    std::ofstream out(outFile);
    for (size_t i = 0; i < sizeof(names) / sizeof(names[0]); ++i) {
        TGraph* g = (TGraph*)f.Get(names[i]);
        if (!g) {
            std::cerr << "missing curve " << names[i] << std::endl;
            continue;
        }
        out << "# curve " << names[i] << "\n";
        for (int p = 0; p < g->GetN(); ++p) {
            double x, y;
            g->GetPoint(p, x, y);
            out << std::setprecision(10) << x << " " << y << "\n";
        }
    }
    out.close();
    std::cout << "wrote " << outFile << std::endl;
}
