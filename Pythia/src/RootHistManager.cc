#include "RootHistManager.h"
#include <stdexcept>


RootHistManager::RootHistManager():
store_(true)
{
}


RootHistManager::RootHistManager(bool store):
store_(store)
{
}


RootHistManager::~RootHistManager()
{
}


void RootHistManager::addHist(TH1* hist)
{
    hists_[hist->GetName()] = hist;
}


void RootHistManager::fillTH1(const std::string hist, const double value, const double weight)
{
    if (store_) {
        checkHistName(hist);
        hists_[hist]->Fill(value, weight);
    }
}


void RootHistManager::fillTH2(const std::string hist, const double valueX, const double valueY, const double weight)
{
    if (store_) {
        checkHistName(hist);
        ((TH2*)hists_[hist])->Fill(valueX, valueY, weight);
    }
}


void RootHistManager::write(TFile* file)
{
    file->cd();
    for (auto & it : hists_) {
        it.second->Write();
    }
}

void RootHistManager::checkHistName(const std::string hist)
{
    if (hists_.find(hist) == hists_.end()) {
        throw std::range_error("No histogram with the name " + hist);
    }
}
