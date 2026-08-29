#include "dybAlphaPeak.h"

int    dybAlphaPeak::s_count    = 0;

dybAlphaPeak::dybAlphaPeak()
{
  //std::cout << " $$ create alpha " << s_count << std::endl;
  s_count++;
}
dybAlphaPeak::dybAlphaPeak(string peakName,double eTru)
{
  //std::cout << " $$ peakName gamma " << s_count << std::endl;
  s_count++;
  Init(peakName,eTru);
}
dybAlphaPeak::~dybAlphaPeak()
{
  //std::cout << " Destroy " << s_count << std::endl;
  s_count--;
}
void dybAlphaPeak::Init(string peakName, double eTru)
{
  m_name         = peakName;
  m_eTru         = eTru;
  //m_dataFullNL   = m_eRec/m_eTru_total;
}
void dybAlphaPeak::SetERec(double val)
{
  m_eRec       = val;
  m_dataFullNL = m_eRec/m_eTru;
}
void dybAlphaPeak::UpdateTheoNL()
{
	m_eVis        = m_eTru*dybEnergyModel::AlphaNL(m_eTru);
	m_theoScintNL = m_eVis/m_eTru;
	m_theoFullNL  = m_eVis*dybEnergyModel::ElectronicsNL(m_eVis)/m_eTru;
}
void dybAlphaPeak::UpdateDataNL()
{
  UpdateTheoNL();
  for (int i = 0; i <100000; i++)
  {
    double eVis = i*0.0001;
    double eRec = eVis*dybEnergyModel::ElectronicsNL(eVis);
    if(eRec>=m_eRec)
    {
      //std::cout << " found " << eVis << std::endl;
      m_dataScintNL = eVis/m_eTru;
      return;
    }
  }
}
double dybAlphaPeak::GetChi2()
{
  UpdateTheoNL();
  double error2 = m_eRecError*m_eRecError;
  return pow( (m_theoFullNL - m_dataFullNL) ,2) / error2;
}

