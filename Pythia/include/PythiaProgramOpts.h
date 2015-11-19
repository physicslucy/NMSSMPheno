#ifndef PYTHIAPROGRAMOPTS_H
#define PYTHIAPROGRAMOPTS_H

#include <iostream>
#include <boost/program_options.hpp>

using std::cout;
using std::endl;

namespace po = boost::program_options;

class PythiaProgramOpts
{
  public:
    // constructor, parses input
    PythiaProgramOpts(int argc, char* argv[]);

    virtual ~PythiaProgramOpts();

    // Getters
    std::string cardName() { return cardName_; }

    int nEvents() { return nEvents_; }

    double mass() { return mass_; }

    int seed() { return seed_; }

    double energy() { return energy_; }

    bool diMuFilter() { return diMuFilter_; }

    bool writeToHEPMC() { return writeToHEPMC_; }

    std::string filenameHEPMC() { return filenameHEPMC_; }

    bool writeToLHE() { return writeToLHE_; }

    std::string filenameLHE() { return filenameLHE_; }

    bool writeToROOT() { return writeToROOT_; }

    std::string filenameROOT() { return filenameROOT_; }

    bool printEvent() { return printEvent_; }

    bool verbose() { return verbose_; }

    bool zip() { return zip_; }

    /**
     * @brief Prints a summary of program options to STDOUT.
     * Useful for start of program.
     */
    void printProgramOptions();

    /**
     * @brief Generate a filename stem.
     * @details <channel>_ma1_<mass>_n<number of events>_seed<seed>
     */
    std::string generateFilenameStem();

  private:
    /**
     * @brief Slightly classier error handling. Prints e.what(), along with a
     * custom error message, and then the standard program usage.
     *
     * @details All printed to STDERR
     *
     * @param e boost::program_options::error object (or derivative)
     * @param message Custom message to print to STDERR.
     */
    void printOptionError(po::error &e, std::string message);

    /**
     * @brief Check whether the filename ends with extension ext.
     *
     * @param filename Filename to check
     * @param ext Extension
     *
     * @return true if filename ends with ext
     */
    static bool checkExtension(std::string filename, std::string ext) ;

    std::string cardName_;
    int nEvents_;
    double mass_;
    int seed_;
    double energy_;
    bool diMuFilter_;

    bool writeToHEPMC_;
    std::string filenameHEPMC_;

    bool writeToLHE_;
    std::string filenameLHE_;

    bool writeToROOT_;
    std::string filenameROOT_;

    bool printEvent_;
    bool verbose_;

    bool zip_;

    po::options_description desc_;
};


#endif
