#include <iostream>
#include <fstream>
#include <string>
#include <thread>
#include <vector>
#include "Pythia8/Pythia.h"
// #include "fastjet/PseudoJet.hh"
// #include "fastjet/ClusterSequence.hh"
#include "Pythia8Plugins/HepMC2.h"

// ROOT headers
#include "TH1.h"
#include "TFile.h"

// Own headers
#include "PythiaProgramOpts.h"

using std::cout;
using std::endl;
using boost::lexical_cast;
using namespace Pythia8;

// Forward declare methods
std::string getCurrentTime();

/**
 * @brief Main function for generating MC events
 */
int main(int argc, char *argv[]) {

  PythiaProgramOpts opts(argc, argv);
  opts.printProgramOptions();

  //---------------------------------------------------------------------------
  // SETUP PYTHIA
  //---------------------------------------------------------------------------
  Pythia pythia;
  pythia.readFile("input_cards/common_pp13.cmnd");
  pythia.readFile(opts.cardName());

  pythia.readString("Main:numberOfEvents = " + lexical_cast<std::string>(opts.nEvents()));
  pythia.readString("Random:seed = " + lexical_cast<std::string>(opts.seed()));
  pythia.readString("36:m0 = " + lexical_cast<std::string>(opts.mass()));

  pythia.init();

  // Interface for conversion from Pythia8::Event to HepMC event.
  HepMC::Pythia8ToHepMC ToHepMC;
  HepMC::IO_GenEvent *ascii_io = nullptr;
  if (opts.writeToHEPMC()) {
    ascii_io = new HepMC::IO_GenEvent(opts.filenameHEPMC(), std::ios::out);
    cout << "Writing HepMC to " << opts.filenameHEPMC() << endl;
  }

  // Create an LHAup object that can access relevant information in pythia for writing to LHE
  LHAupFromPYTHIA8 * myLHA = nullptr;
  if (opts.writeToLHE()) {
    cout << "Writing LHE to " << opts.filenameLHE() << endl;
    // Create an LHAup object that can access relevant information in pythia.
    myLHA = new LHAupFromPYTHIA8(&pythia.process, &pythia.info);
    // Open a file on which LHEF events should be stored, and write header.
    myLHA->openLHEF(opts.filenameLHE());
    // Store initialization info in the LHAup object.
    myLHA->setInit();
    // Write out this initialization info on the file.
    myLHA->initLHEF();
  }

  // Text file to write progress - handy for monitoring during jobs
  ofstream progressFile;
  std::string stem = opts.generateFilename();
  progressFile.open(stem + "_progress.txt");

  //---------------------------------------------------------------------------
  // SETUP PYTHIA HISTOGRAMS
  // very quick n basic, designed for sanity check after running
  //---------------------------------------------------------------------------
  Hist hTransverseMomentum("h transverse momentum", 40, 0, 200);
  Hist a1Separation("a1 separation deltaR", 100, 0, 5);
  Hist a1PhiSeparation("a1 separation deltaPhi", 31, 0, 3.1);
  Hist a1Momentum("a1 momentum", 80, 0, 400);
  Hist a1TransverseMomentum("a1 transverse momentum", 80, 0, 400);
  Hist a1DecayDR("a1 decay product separation deltaR", 100, 0, 5);
  Hist a1DecayDPhi("a1 decay product separation deltaPhi", 31, 0, 3.1);

  //---------------------------------------------------------------------------
  // SETUP ROOT FILES/HISTOGRAMS
  //---------------------------------------------------------------------------
  TFile * outFile = nullptr;
  if (opts.writeToROOT()) {
    outFile = new TFile((opts.generateFilename()+".root").c_str(), "RECREATE");
  }
  TH1F * h_a1Dr = new TH1F("a1Dr","a1 DeltaR", 100, 0, 5);
  TH1F * h_a1DecayDr = new TH1F("a1DecayDr","a1 decay products DeltaR", 100, 0, 5);

  //---------------------------------------------------------------------------
  // GENERATE EVENTS
  //---------------------------------------------------------------------------
  int outputEvery = 50;  // frequency for printing progress updates

  for (int iEvent = 0; iEvent < opts.nEvents(); ++iEvent) {
    // output progress info
    if (iEvent % outputEvery == 0) {
      cout << "iEvent: " << iEvent << " - " << getCurrentTime() << endl;
      progressFile << "iEvent: " << iEvent << " - " << getCurrentTime() << endl;
    }

    // Generate event safely
    if (!pythia.next()) {
      break;
    }

    // Output to screen if wanted
    if (iEvent < 2 && opts.printEvent()) {
      pythia.info.list();
      pythia.event.list();
      pythia.process.list();
    }

    //-------------------------------------------------------------------------
    // Analyse the event particles, fill histograms, etc.
    //-------------------------------------------------------------------------
    bool donePlots = false;

    // find h decay products and look at separation
    for (int i = 0; i < pythia.event.size(); ++i) {
      if (donePlots) break;

      // look at h1, it's daughters, and their daughters
      if (abs(pythia.event[i].id()) == 25 && pythia.event[i].status() == -62) {

        // plot h1 variables
        hTransverseMomentum.fill(pythia.event[i].pT());

        int d1 = pythia.event[i].daughter1();
        int d2 = pythia.event[i].daughter2();
        a1Separation.fill(REtaPhi(pythia.event[d1].p(), pythia.event[d2].p()));
        a1PhiSeparation.fill(phi(pythia.event[d1].p(), pythia.event[d2].p()));

        if (opts.writeToROOT()) {
          h_a1Dr->Fill(REtaPhi(pythia.event[d1].p(), pythia.event[d2].p()));
        }

        // now find all the a1s
        std::vector<Particle*> a1s;
        for (int d = d1; d <= d2; ++d) {
          if (pythia.event[d].id() == 36) {
            a1s.push_back(&pythia.event[d]);
          }
        }

        // now plot a1 variables, and for its decay products
        for (auto & a1 : a1s) {
          a1Momentum.fill(a1->pAbs());
          a1TransverseMomentum.fill(a1->pT());
          // look at a1 daughter particles
          Vec4 daughter1Mom = pythia.event[a1->daughter1()].p();
          Vec4 daughter2Mom = pythia.event[a1->daughter2()].p();
          a1DecayDR.fill(REtaPhi(daughter1Mom, daughter2Mom));
          a1DecayDPhi.fill(phi(daughter1Mom, daughter2Mom));

          if (opts.writeToROOT()){
            h_a1DecayDr->Fill(REtaPhi(daughter1Mom, daughter2Mom));
          }
        }
        donePlots = true;
      }
    }

    //-------------------------------------------------------------------------
    // STORE IN HEPMC/LHE
    //-------------------------------------------------------------------------

    // Construct new empty HepMC event and fill it.
    // Write the HepMC event to file. Done with it.
    if (opts.writeToHEPMC()) {
      HepMC::GenEvent* hepmcevt = new HepMC::GenEvent(HepMC::Units::GEV, HepMC::Units::MM);
      ToHepMC.fill_next_event(pythia, hepmcevt);
      *ascii_io << hepmcevt;
      delete hepmcevt;
    }

    if (opts.writeToLHE()) {
      // Store event info in the LHAup object.
      myLHA->setEvent();
      // Write out this event info on the file.
      // With optional argument (verbose =) false the file is smaller.
      myLHA->eventLHEF();
    }

  } // end of generating events loop


  //---------------------------------------------------------------------------
  // PRINTOUT STATS & HISTOGRAMS
  //---------------------------------------------------------------------------
  pythia.stat();

  cout << hTransverseMomentum << endl;
  cout << a1PhiSeparation << endl;
  cout << a1Separation << endl;
  cout << a1Momentum << endl;
  cout << a1TransverseMomentum << endl;
  cout << a1DecayDR << endl;
  cout << a1DecayDPhi << endl;

  //---------------------------------------------------------------------------
  // WRITE ROOT HISTOGRAMS TO FILE & TIDY UP
  //---------------------------------------------------------------------------
  if (opts.writeToROOT()) {
    h_a1DecayDr->Write();
    h_a1Dr->Write();
    outFile->Close();
    delete outFile;
  }

  progressFile.close();

  if (opts.writeToLHE()) {
    // Update the cross section info based on Monte Carlo integration during run.
    myLHA->updateSigma();
    // Write endtag. Overwrite initialization info with new cross sections.
    myLHA->closeLHEF(true);
    delete myLHA;
  }

  delete ascii_io;
}


/**
 * @brief Get current time & date
 * @return std::string with time & date
 */
std::string getCurrentTime() {
  time_t now = time(0);
  char* dt = ctime(&now);
  std::string str1 = std::string(dt);
  boost::algorithm::trim(str1);
  return str1;
}