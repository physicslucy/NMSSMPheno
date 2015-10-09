#ifndef ROOTHISTMANAGER_H
#define ROOTHISTMANAGER_H

#include <iostream>
#include <map>

#include "TH1.h"
#include "TH2.h"
#include "TFile.h"

using std::cout;
using std::endl;

class RootHistManager
{
    public:
        RootHistManager();
        RootHistManager(bool store);
        virtual ~RootHistManager();
        virtual void addHist(TH1* hist);
        virtual void fillTH1(const std::string hist, const double value, const double weight=1);
        virtual void fillTH2(const std::string hist, const double valueX, const double valueY, const double weight=1);
        virtual void write(TFile* file);
    private:
        virtual void checkHistName(const std::string hist);
        std::map<std::string, TH1*> hists_;
        bool store_;
};

#endif