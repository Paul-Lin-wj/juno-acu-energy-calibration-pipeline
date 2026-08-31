#include "fitter.h"

//dybSpectrum dybGlobalFit::m_b12Spectrum;
int main(int argc, char** argv){ 

	//gStyle->SetTextFont (43);
	//gROOT->SetBatch();
	//TApplication app("app", &argc, argv);
	SetStyle();
	dybEnergyModel::s_p0    = dybParameters::p0_start;
	dybEnergyModel::s_p1    = dybParameters::p1_start;
	dybEnergyModel::s_p2    = dybParameters::p2_start;
	dybEnergyModel::s_p3    = dybParameters::p3_start;
	dybEnergyModel::SetScintP1(dybParameters::p1_start); 
	dybEnergyModel::s_cer   = dybParameters::p2_start;
	dybEnergyModel::s_rad   = dybParameters::p3_start;
	dybEnergyModel::SetKBAlpha(dybParameters::kB_alpha_start); 
												 
	dybEnergyModel::s_alp1  = dybParameters::alpha_start;
	dybEnergyModel::s_tau1  = dybParameters::tau_start;
	dybEnergyModel::s_alp2  = dybParameters::alpha2_start;
	dybEnergyModel::s_tau2  = dybParameters::tau2_start;
	
	dybSpectrum::s_n12Ratio = dybParameters::n12Ratio;
	dybSpectrum::s_c10C11Frac = dybParameters::c10C11Frac_start;
	dybSpectrum::s_c10Be11Frac = dybParameters::c10Be11Frac_start;
	dybSpectrum::s_b12Branch0 = dybParameters::b12Branch0;
	dybSpectrum::s_b12Branch1 = dybParameters::b12Branch1;
	dybSpectrum::s_b12Branch2 = dybParameters::b12Branch2;
	dybSpectrum::s_n12Branch0 = dybParameters::n12Branch0;
	dybSpectrum::s_n12Branch1 = dybParameters::n12Branch1;
	dybSpectrum::s_n12Branch2 = dybParameters::n12Branch2;
	dybSpectrum::s_n12Branch3 = dybParameters::n12Branch3;
	dybSpectrum::s_n12Branch4 = dybParameters::n12Branch4;
	
	//dybGammaData gammaData;
	//gammaData.LoadData(dybParameters::gammaData_file  );
	
	//globalFit.GenToyMC();
	//globalFit.LoadToyMC(0);
	
	//dybB12Data b12;
	//b12.LoadData(dybParameters::b12Data_file);
	//b12.Plot(0);

	dybGlobalFit globalFit;
	globalFit.LoadData();
        //globalFit.Plot();
	//return 1;
	globalFit.Fit();
        std::cout<<"running WriteResult()"<<std::endl;
	globalFit.WriteResult();
        std::cout<<"running Plot()"<<std::endl;
	globalFit.Plot();

	std::cout<<"running dybEnergyModel::SaveCurves()"<<std::endl;
        dybEnergyModel::SaveCurves();

	// CL band: 0 upstream disables the sampling loop in DrawErrors().
	// Env opt-in (used by the pipeline's error-band runs): the fit path
	// (Fit/WriteResult/SaveCurves) is untouched, only the number of
	// GetCLSample() curve samples after it changes.
	const char* clItr = getenv("CL_CONTOUR_NITR");
	if (clItr && atoi(clItr) > 0) {
		std::cout<<"CL_CONTOUR_NITR="<<clItr<<" — enabling error band"<<std::endl;
		globalFit.SetContourNItr(atoi(clItr));
	}
        std::cout<<"running dybEnergyModel::DrawErrors()"<<std::endl;
        globalFit.DrawErrors();
	return 1;
}
 
