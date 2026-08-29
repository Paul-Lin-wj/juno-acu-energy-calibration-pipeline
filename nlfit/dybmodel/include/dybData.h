#ifndef dybData_h
#define dybData_h

#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <math.h>
#include <dirent.h>
#include <unistd.h>

using namespace std;

class dybData
{
  public:
    virtual void   LoadData(string fileName) = 0;
    virtual double GetChi2 (int nDoF = 0) = 0;
    virtual void   GenToyMC() = 0;
    int GetNData() {return m_nData;}
    
  protected:
    static int s_toyMCCount;
    int m_nData;
};

#endif
