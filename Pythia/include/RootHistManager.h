#ifndef ROOTHISTMANAGER_H
#define ROOTHISTMANAGER_H

#include <iostream>
#include <map>

#include "TH1.h"
#include "TH2.h"
#include "TFile.h"

using std::cout;
using std::endl;

/**
 * @brief This is a utility class designed to handle the filling of histograms,
 * and their saving to file. The ctor takes an argument that allows for filling
 * of hists or bypassing them. This way the main code can avoid lots of
 * spurious if( )... statements. All the user has to do is make the new hist
 * objects, add them to the manager, then fill them later.
 * Finally, they can be written to file in one go.
 */
class RootHistManager
{
    public:
        /**
         * @brief Default ctor. Will store values in hists.
         */
        RootHistManager();

        /**
         * @brief Ctor with switch for storing or ignoring.
         *
         * @param store true to store values in hists, false to bypass filling.
         */
        RootHistManager(bool store);

        virtual ~RootHistManager();

        /**
         * @brief Add a histogram to the manager. Must be done before
         * fillX() can be called.
         *
         * @param hist Any object that inherits from TH1.
         */
        virtual void addHist(TH1* hist);

        /**
         * @brief Fill a 1D histogram, with optional weight. Will throw
         * std::range_error if no histogram exists with the name provided.
         *
         * @param hist Name of histogram (i.e. returned by hist.GetName())
         * @param value Value to add to histgoram.
         * @param weight Optional weight. Default = 1.
         */
        virtual void fillTH1(const std::string hist, const double value, const double weight=1);

        /**
         * @brief Fill a 2D histogram, with optional weight. Will throw
         * std::range_error if no histogram exists with the name provided.
         *
         * @param hist Name of histogram (i.e. returned by hist.GetName())
         * @param valueX X value to add to histgoram.
         * @param valueY Y value to add to histgoram.
         * @param weight Optional weight. Default = 1.
         */
        virtual void fillTH2(const std::string hist, const double valueX, const double valueY, const double weight=1);

        /**
         * @details Write all histograms to ROOT file.
         *
         * @param file Opened TFile, must be able to write-able.
         */
        virtual void write(TFile* file);
    private:
        /**
         * @brief Check if histogram with given name exists in manager object.
         * Will throw std::range_error if no histogram exists with the name provided.
         *
         * @param hist Name of histogram object.
         */
        virtual void checkHistName(const std::string hist);

        std::map<std::string, TH1*> hists_; // store the hists
        bool store_; // true to fill hists
};

#endif