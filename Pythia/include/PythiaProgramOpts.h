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
using std::cerr;
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
      cardName_(""),
      nEvents_(1),
      mass_(8.),
      seed_(0),
      writeToHEPMC_(false),
      filenameHEPMC_(""),
      writeToLHE_(false),
      filenameLHE_(""),
      writeToROOT_(false),
      filenameROOT_(""),
      printEvent_(false),
      verbose_(false)
    {
      po::options_description desc("\nProduces 13 TeV MC for p-p collisions.\n"
        "User must specify the physics process(es) to be generated \nvia an input"
        " card (see input_cards directory for examples).\nDefaults for beams, "
        "PDF, etc are set in input_cards/common_pp13.cmnd\n\nAllowed options:");

      std::string defaultFile = "<card>_ma1_<mass>_<seed>";

      desc.add_options()
        ("help,h", "Produce help message")
        ("card", po::value<std::string>(&cardName_)->required(),
          "Name of Pythia8 settings card to loads physics processes")
        ("number,n", po::value<int>(&nEvents_)->default_value(nEvents_),
          "Number of events to run over [default = 1]. ")
        ("mass", po::value<double>(&mass_)->default_value(mass_),
          "Mass of a1 boson in GeV")
        ("seed", po::value<int>(&seed_)->default_value(seed_),
          "Seed for random number generator. 0 = uses time. " \
          "WARNING: DON'T USE 0 FOR BATCH SYSTEM. " \
          "Get simultaneous start = same seed = same events. " \
          "Set seed explicitly instead (e.g. file number).")
        ("hepmc", po::value<std::string>(&filenameHEPMC_)->implicit_value(filenameHEPMC_),
          "Save output in HepMC format (includes hadronisation). " \
          "Can optionally take a filename for the HepMC file. "\
          "If you don't provide a filename, " \
          "the default filename will be <card>_ma1_<mass>_<seed>.hepmc")
        ("lhe", po::value<std::string>(&filenameLHE_)->implicit_value(filenameLHE_),
          "Save output in LHE format (hard process only). " \
          "Can optionally take a filename for the LHE file. "\
          "If you don't provide a filename, " \
          "the default filename will be <card>_ma1_<mass>_<seed>.lhe")
        ("root", po::value<std::string>(&filenameROOT_)->implicit_value(filenameROOT_),
          "Save plots to ROOT file. " \
          "Can optionally take a filename for the ROOT file. "\
          "If you don't provide a filename, " \
          "the default filename will be <card>_ma1_<mass>_<seed>.root")
        ("printEvent", po::bool_switch(&printEvent_)->default_value(printEvent_),
          "Prints complete event listing of first event to screen")
        ("verbose,v", po::bool_switch(&verbose_)->default_value(verbose_),
          "Output debugging statements")
      ;

      po::variables_map vm;
      try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
      } catch (po::invalid_option_value e) {
        printOptionError(e, "Invalid option value", desc);
      } catch (po::unknown_option e) {
        printOptionError(e, "Unrecognised option", desc);
      } catch (po::invalid_command_line_syntax e) {
        printOptionError(e, "Invalid command line syntax", desc);
      } catch (boost::program_options::required_option e) {
        printOptionError(e, "Required option missing", desc);
      } catch (po::error e) {
        // should I just use this one?
        printOptionError(e, "Error in program_options", desc);
      }

      po::notify(vm);

      if (vm.count("help")) {
        cout << desc << endl;
        exit(1);
      }

      // Check input card exists
      if (!fs::exists(fs::path(cardName_))) {
        throw std::runtime_error("Input card \"" + cardName_+ "\" does not exist");
      }

      // Handle output filenames for various formats
      if (vm.count("hepmc")) {
        writeToHEPMC_ = true;
        // Generate default filename if necessary
        if (filenameHEPMC_ == "") {
          filenameHEPMC_ = generateFilename() + ".hepmc";
        }
        // Check if there's already an extension on filename, if not add one
        if(!PythiaProgramOpts::checkExtension(filenameHEPMC_, ".hepmc")) {
          filenameHEPMC_ += ".hepmc";
        }
      }

      if (vm.count("lhe")) {
        writeToLHE_ = true;
        // Generate default filename if necessary
        if (filenameLHE_ == "") {
          filenameLHE_ = generateFilename() + ".lhe";
        }
        // Check if there's already an extension on filename, if not add one
        if(!PythiaProgramOpts::checkExtension(filenameLHE_, ".lhe")) {
          filenameLHE_ += ".lhe";
        }
      }

      if (vm.count("root")) {
        writeToROOT_ = true;
        // Generate default filename if necessary
        if (filenameROOT_ == "") {
          filenameROOT_ = generateFilename() + ".root";
        }
        // Check if there's already an extension on filename, if not add one
        if(!PythiaProgramOpts::checkExtension(filenameROOT_, ".root")) {
          filenameROOT_ += ".root";
        }
      }

    } // end of constructor

    // Getters
    std::string cardName() { return cardName_; }

    int nEvents() { return nEvents_; }

    double mass() { return mass_; }

    int seed() { return seed_; }

    bool writeToHEPMC() { return writeToHEPMC_; }

    std::string filenameHEPMC() { return filenameHEPMC_; }

    bool writeToLHE() { return writeToLHE_; }

    std::string filenameLHE() { return filenameLHE_; }

    bool writeToROOT() { return writeToROOT_; }

    std::string filenameROOT() { return filenameROOT_; }

    bool printEvent() { return printEvent_; }

    bool verbose() { return verbose_; }

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
      if (writeToROOT_)
        cout << "Saving histograms to ROOT file " << filenameROOT_ << endl;
      cout << "Generating " << nEvents_ << " events" << endl;
      cout << "Random seed: " << seed_ << endl;
      cout << "Mass of a1: " << mass_ << endl;
      cout << "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++" << endl;
    }

    std::string generateFilename() {
      std::string channel = fs::path(cardName_).stem().string();
      return channel + "_ma1_" + lexical_cast<std::string>(mass_) + "_" + lexical_cast<std::string>(seed_);
    }

  private:

    void printOptionError(po::error &e, std::string message, po::options_description desc) {
      cerr << message << ": " << e.what() << endl;
      cerr << desc << endl;
      cerr << "Exiting" << endl;
      exit(1);
    }

    static bool checkExtension(std::string filename, std::string ext) {
      boost::algorithm::to_lower(filename);
      return boost::algorithm::ends_with(filename, ext);
    }

    std::string cardName_;
    int nEvents_;
    double mass_;
    int seed_;

    bool writeToHEPMC_;
    std::string filenameHEPMC_;

    bool writeToLHE_;
    std::string filenameLHE_;

    bool writeToROOT_;
    std::string filenameROOT_;

    bool printEvent_;
    bool verbose_;
};


#endif
