#ifndef PYTHIAPROGRAMOPTS_H
#define PYTHIAPROGRAMOPTS_H

#include <iostream>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>
#include <boost/system/error_code.hpp>

using std::cout;
using std::endl;
using boost::lexical_cast;
namespace fs = boost::filesystem;
namespace po = boost::program_options;
namespace bs = boost::system;

class PythiaProgramOpts
{
  public:
    // constructor, parses input
    PythiaProgramOpts(int argc, char* argv[]):
      printEvent_(false),
      writeToHEPMC_(false),
      writeToLHE_(false),
      nEvents_(1),
      filenameHEPMC_(""),
      filenameLHE_(""),
      mass_(15.),
      verbose_(false),
      seed_(0),
      rootHists_(false),
      cardName_("")
    {
      po::options_description desc("\nProduces gg -> h(125) -> AA, with " \
        "A->2b or A-> 2 tau.\nAllowed options:");
      desc.add_options()
        ("help,h", "Produce help message")
        ("printEvent", po::bool_switch(&printEvent_)->default_value(printEvent_),
          "Prints complete event listing of first event to screen")
        ("hepmc", po::bool_switch(&writeToHEPMC_)->default_value(writeToHEPMC_),
          "write events to file in HepMC format")
        ("lhe", po::bool_switch(&writeToLHE_)->default_value(writeToLHE_),
          "write events to file in LHE format")
        ("number,n", po::value<int>(&nEvents_)->default_value(nEvents_),
          "Number of events to run over [default = 1]. " \
          "If writeHLT enabled, counts # events passing HLT. " \
          "Otherwise, counts # events with 2+ muons.")
        ("nameHEPMC", po::value<std::string>(&filenameHEPMC_),
          "Filename for output HepMC filename. " \
          "If you don't provide a value but enable --hepmc, " \
          "the default filename will be ma1_<mass>_<seed>.hepmc")
        ("nameLHE", po::value<std::string>(&filenameLHE_),
          "Filename for output LHE filename. " \
          "If you don't provide a value but enable --lhe, " \
          "the default filename will be ma1_<mass>_<seed>.lhe")
        ("mass", po::value<double>(&mass_)->default_value(mass_),
          "Mass of a1 boson in GeV")
        ("seed", po::value<int>(&seed_)->default_value(seed_),
          "Seed for random number generator. 0 = uses time. " \
          "WARNING: DON'T USE 0 FOR BATCH SYSTEM. " \
          "Get simultaneous start = same seed = same events. " \
          "Set seed explicitly instead (e.g. file number).")
        ("verbose,v", po::bool_switch(&verbose_)->default_value(verbose_),
          "Output debugging statements")
        ("root", po::bool_switch(&rootHists_)->default_value(rootHists_),
          "Save quantities in ROOT histograms. Handy for debugging.")
        ("card", po::value<std::string>(&cardName_),
          "Name of Pythia8 settings card to loads Physics processes")
      ;

      po::variables_map vm;
      try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
      } catch (boost::program_options::invalid_option_value e) {
        cout << "Invalid option value: " << e.what() << endl;
        cout << desc << endl;
        cout << "Exiting" << endl;
        exit(1);
      } catch (boost::program_options::unknown_option e) {
        cout << "Unrecognised option: " << e.what() << endl;
        cout << desc << endl;
        cout << "Exiting" << endl;
        exit(1);
      }

      po::notify(vm);

      if (vm.count("help")) {
        cout << desc << endl;
        exit(1);
      }

      // make physics input card part of filename
      // fs::path p(cardName_);
      std::string channel = fs::path(cardName_).stem().string();

      // Setup filenames
      if (filenameHEPMC_ == "") {
        filenameHEPMC_ = "ma1_" + lexical_cast<std::string>(mass_) + "_" +
                      channel + "_" + lexical_cast<std::string>(seed_) + ".hepmc";
      }
      if (filenameLHE_ == "") {
        filenameLHE_ = "ma1_" + lexical_cast<std::string>(mass_) + "_" +
                      channel + "_" + lexical_cast<std::string>(seed_) + ".lhe";
      }

      // Check if there's already an extension on filename, if not add one
      std::string filenameHEPMClower(filenameHEPMC_);
      boost::algorithm::to_lower(filenameHEPMClower);
      if(!boost::algorithm::ends_with(filenameHEPMClower, ".hepmc")) {
        filenameHEPMC_ += ".hepmc";
      }

      // Check if there's already an extension on filename, if not add one
      std::string filenameLHElower(filenameLHE_);
      boost::algorithm::to_lower(filenameLHElower);
      if(!boost::algorithm::ends_with(filenameLHElower, ".lhe")) {
        filenameLHE_ += ".lhe";
      }

    } // end of constructor

    // Getters
    bool printEvent() { return printEvent_; }
    bool writeToHEPMC() { return writeToHEPMC_; }
    bool writeToLHE() { return writeToLHE_; }
    int nEvents() { return nEvents_; }
    std::string filenameHEPMC() { return filenameHEPMC_; }
    std::string filenameLHE() { return filenameLHE_; }
    double mass() { return mass_; }
    bool verbose() { return verbose_; }
    int seed() { return seed_; }
    bool root() { return rootHists_; }
    std::string cardName() { return cardName_; }

    // This should really be in a separate .cc file...
    void printProgramOptions() {
      cout << "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" << endl;
      cout << "PYTHIA PROGRAM OPTIONS" << endl;
      cout << "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" << endl;
      cout << "Reading settings from " << cardName_ << endl;
      if (writeToHEPMC_)
        cout << "Writing events to hepmc file " << filenameHEPMC_ << endl;
      if (writeToLHE_)
        cout << "Writing events to lhe file " << filenameLHE_ << endl;
      cout << "Generating " << nEvents_ << " events" << endl;
      cout << "Random seed: " << seed_ << endl;
      // cout << "Mass of h1: " << mass_ << endl;
      cout << "Mass of a1: " << mass_ << endl;
      cout << "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" << endl;
    }

  private:
    bool printEvent_;
    bool writeToHEPMC_;
    bool writeToLHE_;
    int nEvents_;
    std::string filenameHEPMC_;
    std::string filenameLHE_;
    double mass_;
    bool verbose_;
    int seed_;
    bool rootHists_;
    std::string cardName_;
};

#endif
