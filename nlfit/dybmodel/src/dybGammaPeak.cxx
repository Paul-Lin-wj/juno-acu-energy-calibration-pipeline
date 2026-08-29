#include "dybGammaPeak.h"

//double dybGammaPeak::s_gamScale = dybParameters::gamScale_start;
double dybGammaPeak::s_gamScale = 1.0;
double dybGammaPeak::s_reflectivity = 0.0;
int    dybGammaPeak::s_count    = 0;

dybGammaPeak::dybGammaPeak()
{
  //std::cout << " $$ create gamma " << s_count << std::endl;
  s_count++;
}
dybGammaPeak::dybGammaPeak(string peakName,
                           string pdfName,
                           double eTru_total, 
                           double eTru_single)
{
  //std::cout << " $$ peakName gamma " << s_count << std::endl;
  s_count++;
  Init(peakName,pdfName,eTru_total,eTru_single);
}
dybGammaPeak::~dybGammaPeak()
{
  //std::cout << " Destroy " << s_count << std::endl;
  s_count--;
}
void dybGammaPeak::Init(string peakName,
                        string pdfName,
                        double eTru_total,
                        double eTru_single)
{
  m_name         = peakName;
  m_eTru_total   = eTru_total;
  m_eTru_single  = eTru_single;
  //m_dataFullNL   = m_eRec/m_eTru_total;
  m_eVisError    = 0;
  m_nPdf         = 0;
  m_nPdf_anchor  = 0;
  m_biasOS       = 0;
  m_includeInFit = true;
  TFile file(dybParameters::gammaPdf_file.c_str(),"read");
  if (m_name.find("Gd") != std::string::npos)
  {
    TH1F* pdfH   = (TH1F*)file.Get("hEnGd_g4_rmAbnGam");
    TH1F* pdfH2  = (TH1F*)file.Get("hEnGd_g4_onlyPhEv");
    TH1F* pdfH3  = (TH1F*)file.Get("hEnGd_caltech");
    TH1F* pdfH4  = (TH1F*)file.Get("hEnGd_g4_rmAbnGam_enCon");
    //TH1F* pdfH   = (TH1F*)file.Get("hEnGd_g4_old");
    //TH1F* pdfH2  = (TH1F*)file.Get("hEnGd_g4_old");
    //TH1F* pdfH3  = (TH1F*)file.Get("hEnGd_g4_old");
    //TH1F* pdfH4  = (TH1F*)file.Get("hEnGd_g4_old");
    
    //TH1F* pdfH   = (TH1F*)file.Get("hEnGd_g4_rmAbnGam_enCon");
    //TH1F* pdfH2  = (TH1F*)file.Get("hEnGd_g4_rmAbnGam_enCon");
    //TH1F* pdfH3  = (TH1F*)file.Get("hEnGd_g4_rmAbnGam_enCon");
    //TH1F* pdfH4  = (TH1F*)file.Get("hEnGd_g4_rmAbnGam_enCon");
    
    //TH1F* pdfH  = (TH1F*)file.Get("hEnGd_default");
    //TH1F* pdfH2 = (TH1F*)file.Get("hEnGd_default");
    for(int i=0; i<pdfH->GetNbinsX(); i++)
    {
      m_pdf_eTru [i] = pdfH ->GetBinCenter (i+1);
      m_pdf_prob [i] = pdfH ->GetBinContent(i+1);
      m_pdf_prob2[i] = pdfH2->GetBinContent(i+1);
      m_pdf_prob3[i] = pdfH3->GetBinContent(i+1);
      m_pdf_prob4[i] = pdfH4->GetBinContent(i+1);
      //m_pdf_prob5[i] = pdfH5->GetBinContent(i+1);
      if(m_pdf_prob [i]>0 || m_pdf_prob2[i]>0 ||
         m_pdf_prob3[i]>0 || m_pdf_prob4[i]>0 )
         //m_pdf_prob5[i]>0 ) m_nPdf = i;
         m_nPdf = i;
    }
	  delete pdfH;
	  delete pdfH2;
	  delete pdfH3;
	  delete pdfH4;
	  //delete pdfH5;
    if(!dybParameters::fitNGd) m_includeInFit = false;
  }
  else
  {
    TH1F* pdfH  = (TH1F*)file.Get(pdfName.c_str());
    for(int i=0; i<pdfH->GetNbinsX(); i++)
    {
      m_pdf_eTru[i] = pdfH->GetBinCenter (i+1);
      m_pdf_prob[i] = pdfH->GetBinContent(i+1);
      if(m_pdf_prob[i]>0) m_nPdf = i;
    }
	  delete pdfH;
  }

  m_eTru_total_anchor = dybParameters::anchorEnergy;
    TH1F* pdfH_anchor  = (TH1F*)file.Get("hEnH");
    for(int i=0; i<pdfH_anchor->GetNbinsX(); i++)
    {
      m_pdf_eTru_anchor[i] = pdfH_anchor->GetBinCenter (i+1);
      m_pdf_prob_anchor[i] = pdfH_anchor->GetBinContent(i+1);
      if(m_pdf_prob_anchor[i]>0) m_nPdf_anchor = i;
    }
	  delete pdfH_anchor;
    m_eRec_anchor = dybParameters::anchorEnergy;
}
void dybGammaPeak::SetERec(double val)
{
  //m_eRec    = val;
  m_eRecRaw    = val;
  m_eRec       = m_eRecRaw * s_gamScale;
  //double refLosses = 0.01*(1.-s_reflectivity);
  //m_eRec += refLosses*m_eRec;
  double biasOS = m_eRec*m_biasOS*s_reflectivity;
  m_eRec += biasOS;
  m_dataFullNL = m_eRec/m_eTru_total;
}
double dybGammaPeak::GetEffectiveEnergy()
{
  if(IsSingleGamma()) return m_eTru_single;
  UpdateTheoNL();
  TGraph gamNL = dybEnergyModel::DrawGammaScintNL();
  for (int i = 0; i <1000000; i++)
  {
    double eEff = i*0.0001;
    double nl = gamNL.Eval(eEff,0,"S");
    if(nl>=m_theoScintNL)
      return eEff;
  }
}
void dybGammaPeak::UpdateTheoNL()
{
  //if(!m_includeInFit) return;
  m_eRec      = s_gamScale * m_eRecRaw;
  //double refLosses = 0.01*(1.-s_reflectivity);
  //m_eRec += refLosses*m_eRec;
  double biasOS = m_eRec*m_biasOS*s_reflectivity;
  m_eRec += biasOS;
  m_dataFullNL = m_eRec/m_eTru_total;

  /*
  m_dataFullNL_anchor = s_gamScale * m_eRec_anchor/m_eTru_total_anchor;
  m_dataFullNL /= m_dataFullNL_anchor;
  */

  m_eVis      = 0;
  m_eVisError = 0;
  double eTru = 0;
  double prob = 0;
  double sum  = 0;

  //Anchor Nonlinearity at nH energy
  m_eVis_anchor = 0;
  for (int i = 0; i < (int)m_nPdf_anchor - 1; ++i)   
  //for(int i=0; i<m_nPdf_anchor+1; i++)   
  {
    eTru    = m_pdf_eTru_anchor[i];
    prob    = m_pdf_prob_anchor[i];
    sum    += eTru*prob;
    m_eVis_anchor += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob;
  }
  m_eVis_anchor *= m_eTru_total_anchor/sum;
  //m_theoScintNL_anchor = m_eVis_anchor/sum;
  //m_theoFullNL_anchor = m_eVis_anchor/sum;

  if(m_eTru_total_anchor>1.01 && m_eTru_total_anchor<1.02) m_eVis_anchor *= 2.0;
  m_theoScintNL_anchor = m_eVis_anchor/m_eTru_total_anchor;
  m_theoFullNL_anchor  = m_eVis_anchor*dybEnergyModel::ElectronicsNL(m_eVis_anchor)/m_eTru_total_anchor;

  eTru = prob = sum = 0;
  for (int i = 0; i < (int)m_nPdf - 1; ++i)   
  //for(int i=0; i<m_nPdf+1; i++)   
  {
    eTru    = m_pdf_eTru[i];
    prob    = m_pdf_prob[i];
    sum    += eTru*prob;
    m_eVis += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob;
  }
  //std::cout << " ----------->> " << std::endl;
  //std::cout <<m_name << ": " <<  m_eTru_total << ": " << m_eTru_total/sum << std::endl;
  m_eVis *= m_eTru_total/sum;

  //if (m_name.find("C*") != std::string::npos) m_eVis *= m_eTru_total/sum;
  //if (m_name.find("Gd") != std::string::npos) m_eVis *= m_eTru_total/sum;
  //if (m_name.find("68") != std::string::npos) m_eVis *= 2.;
  if (m_name.find("Gd") != std::string::npos)
  {
    double eVis2 = 0;
    double eVis3 = 0;
    double eVis4 = 0;
    //double eVis5 = 0;
    double sum2  = 0;
    double sum3  = 0;
    double sum4  = 0;
    //double sum5  = 0;
    double prob2 = 0;
    double prob3 = 0;
    double prob4 = 0;
    //double prob5 = 0;
    for (int i = 0; i < (int)m_nPdf - 1; ++i)   
    {
      eTru    = m_pdf_eTru [i];
      prob2    = m_pdf_prob2[i];
      prob3    = m_pdf_prob2[i];
      prob4    = m_pdf_prob2[i];
      //prob5    = m_pdf_prob2[i];
      sum2    += eTru*prob2;
      sum3    += eTru*prob3;
      sum4    += eTru*prob4;
      //sum5    += eTru*prob5;
      eVis2  += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob2;
      eVis3  += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob3;
      eVis4  += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob4;
      //eVis5  += eTru * dybEnergyModel::ScintillatorNL(eTru) * prob5;
    }
    eVis2 *= m_eTru_total/sum2;
    eVis3 *= m_eTru_total/sum3;
    eVis4 *= m_eTru_total/sum4;
    //eVis5 *= m_eTru_total/sum5;
    m_eVis = (m_eVis+eVis2+eVis3+eVis4)/4.;
    m_eVisError = fabs(m_eVis-eVis2);
    if(fabs(m_eVis-eVis3)>m_eVisError) m_eVisError = fabs(m_eVis-eVis3);
    if(fabs(m_eVis-eVis4)>m_eVisError) m_eVisError = fabs(m_eVis-eVis4);
    //if(fabs(m_eVis-eVis5)>m_eVisError) m_eVisError = fabs(m_eVis-eVis5);
    m_eVisError  /= m_eTru_total;
    //m_eVisError += 0.005;
    m_eVisError += 0.0035;
    //m_eVisError = 0.002;
  }
  if(m_eTru_total>1.01 && m_eTru_total<1.02) m_eVis *= 2.0;
  m_theoScintNL = m_eVis/m_eTru_total;
  m_theoFullNL  = m_eVis*dybEnergyModel::ElectronicsNL(m_eVis)/m_eTru_total;
  //anchor
  //m_theoFullNL /= m_theoFullNL_anchor;
  //m_theoScintNL = m_theoFullNL/dybEnergyModel::ElectronicsNL(m_eVis);
}
void dybGammaPeak::UpdateDataNL()
{
  UpdateTheoNL();
  //m_eRec      = s_gamScale * m_eRecRaw;
  //std::cout << " ----> rec " << m_eRec <<  std::endl;
  for (int i = 0; i <100000; i++)
  {
    double eVis = i*0.0001;
    double eRec = eVis*dybEnergyModel::ElectronicsNL(eVis);
    if(eRec>=m_eRec)
    {
      //std::cout << " found " << eVis << std::endl;
      m_dataScintNL = eVis/m_eTru_total;
      return;
    }
  }
}
double dybGammaPeak::GetChi2()
{
  UpdateTheoNL();
  if(!m_includeInFit) return 0;
  double error2 = m_eRecError*m_eRecError + m_eVisError*m_eVisError;
  //return pow( (m_theoScintNL - m_dataFullNL) ,2) / error2;
  return pow( (m_theoFullNL - m_dataFullNL) ,2) / error2;
}

