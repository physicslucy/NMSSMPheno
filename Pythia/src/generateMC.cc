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

// BOOST headers
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/lexical_cast.hpp>

// Own headers
#include "PythiaProgramOpts.h"
#include "RootHistManager.h"

using std::cout;
using std::endl;
using boost::lexical_cast;
using namespace Pythia8;

// Forward declare methods
std::vector<Particle*> getChildren(Event & event, Particle * p);
std::vector<Particle*> getAllDescendants(Event & event, Particle * p, bool finalStateOnly);
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
  HepMC::IO_GenEvent ascii_io(opts.filenameHEPMC(), std::ios::out);
  if (opts.writeToHEPMC()) {
    cout << "Writing HepMC to " << opts.filenameHEPMC() << endl;
  }

  // Create an LHAup object that can access relevant information in pythia for writing to LHE
  LHAupFromPYTHIA8 myLHA(&pythia.process, &pythia.info);
  if (opts.writeToLHE()) {
    // myLHA2.reset();
    cout << "Writing LHE to " << opts.filenameLHE() << endl;
    // Open a file on which LHEF events should be stored, and write header.
    myLHA.openLHEF(opts.filenameLHE());
    // Store initialization info in the LHAup object.
    myLHA.setInit();
    // Write out this initialization info on the file.
    myLHA.initLHEF();
  }

  // Text file to write progress - handy for monitoring during jobs
  ofstream progressFile;
  std::string stem = opts.generateFilenameStem();
  progressFile.open(stem + "_progress.txt");

  //---------------------------------------------------------------------------
  // SETUP PYTHIA HISTOGRAMS
  // very quick n basic, designed for sanity check after running
  //---------------------------------------------------------------------------
  Hist hPt("h transverse momentum", 40, 0, 200);
  Hist a1DR("a1 separation deltaR", 100, 0, 5);
  Hist a1DPhi("a1 separation deltaPhi", 31, 0, 3.1);
  Hist a1Eta("a1 pseudorapidity", 100, -5, 5);
  Hist a1Pt("a1 transverse momentum", 80, 0, 400);
  Hist a1DecayDR("a1 decay product separation deltaR", 100, 0, 5);
  Hist a1DecayDPhi("a1 decay product separation deltaPhi", 31, 0, 3.1);

  //---------------------------------------------------------------------------
  // SETUP ROOT FILES/HISTOGRAMS
  //---------------------------------------------------------------------------
  RootHistManager histMan(opts.writeToROOT());
  histMan.addHist(new TH1F("hPt","h pT", 300, 0, 300));
  histMan.addHist(new TH1F("a1Pt","a1 pT", 400, 0, 400));
  histMan.addHist(new TH1F("a1Eta","a1 pseudorapidity", 500, -5, 5));
  histMan.addHist(new TH1F("a1Dr","a1 DeltaR", 500, 0, 5));
  histMan.addHist(new TH1F("a1DecayDr","a1 decay products DeltaR", 1000, 0, 5));
  histMan.addHist(new TH1F("a1DecayPt","a1 decay products pT", 400, 0, 400));
  histMan.addHist(new TH1F("a1DecayEta","a1 decay products pseudorapidity", 500, -5, 5));

  //---------------------------------------------------------------------------
  // GENERATE EVENTS
  //---------------------------------------------------------------------------
  int progressFreq = 50;

  for (int iEvent = 0; iEvent < opts.nEvents(); ++iEvent) {
    // output progress info
    if (iEvent % progressFreq == 0) {
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

    Event & event = pythia.event;

    // find h decay products and look at separation
    for (int i = 0; i < event.size(); ++i) {
      if (donePlots) break; // skip the rest of the event listing, we're done


      // look at h1, its daughters (a1), and their daughters (tau, b, etc)
      if (abs(event[i].id()) == 25 && event[i].status() == -62) {
        Particle & h1 = event[i];

        // plot h1 variables
        hPt.fill(h1.pT());

        int d1 = h1.daughter1();
        int d2 = h1.daughter2();
        a1DR.fill(REtaPhi(event[d1].p(), event[d2].p()));
        a1DPhi.fill(phi(event[d1].p(), event[d2].p()));

        histMan.fillTH1("hPt", h1.pT());
        histMan.fillTH1("a1Dr", REtaPhi(event[d1].p(), event[d2].p()));

        // now find all the h1 children (e.g. a1)
        std::vector<Particle*> a1s = getChildren(event, &h1);

        // now plot child variables, and its decay products
        for (auto & a1 : a1s) {
          a1Eta.fill(a1->eta());
          a1Pt.fill(a1->pT());
          histMan.fillTH1("a1Pt", a1->pT());
          histMan.fillTH1("a1Eta", a1->eta());

          // look at a1 daughter particles
          Vec4 daughter1Mom = event[a1->daughter1()].p();
          Vec4 daughter2Mom = event[a1->daughter2()].p();
          a1DecayDR.fill(REtaPhi(daughter1Mom, daughter2Mom));
          a1DecayDPhi.fill(phi(daughter1Mom, daughter2Mom));
          histMan.fillTH1("a1DecayDr", REtaPhi(daughter1Mom, daughter2Mom));
          histMan.fillTH1("a1DecayPt", daughter1Mom.pT());
          histMan.fillTH1("a1DecayPt", daughter2Mom.pT());
          histMan.fillTH1("a1DecayEta", daughter1Mom.eta());
          histMan.fillTH1("a1DecayEta", daughter2Mom.eta());
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
      ascii_io << hepmcevt;
      delete hepmcevt;
    }

    if (opts.writeToLHE()) {
      // Store event info in the LHAup object.
      myLHA.setEvent();
      // Write out this event info on the file.
      // With optional argument (verbose =) false the file is smaller.
      myLHA.eventLHEF();
    }

  } // end of generating events loop

  progressFile.close();

  //---------------------------------------------------------------------------
  // PRINTOUT STATS & HISTOGRAMS
  //---------------------------------------------------------------------------
  pythia.stat();

  cout << hPt << endl;
  cout << a1DPhi << endl;
  cout << a1DR << endl;
  cout << a1Eta << endl;
  cout << a1Pt << endl;
  cout << a1DecayDR << endl;
  cout << a1DecayDPhi << endl;

  //---------------------------------------------------------------------------
  // WRITE ROOT HISTOGRAMS TO FILE & TIDY UP
  //---------------------------------------------------------------------------
  if (opts.writeToROOT()) {
      TFile * outFile = new TFile((opts.filenameROOT()).c_str(), "RECREATE");
      histMan.write(outFile);
      outFile->Close();
      delete outFile;
  }

  if (opts.writeToLHE()) {
    // Update the cross section info based on Monte Carlo integration during run.
    myLHA.updateSigma();
    // Write endtag. Overwrite initialization info with new cross sections.
    myLHA.closeLHEF(true);
  }

}


/**
 * @brief Return vector of Particle pointers to 'children' of the particle.
 *
 * @param event Pythia8::Event object holding particle listings
 * @param p Particle to get children.
 *
 * @return
 */
std::vector<Particle*> getChildren(Event & event, Particle * p) {
  std::vector<Particle*> children;
  for (int child = p->daughter1(); child <= p->daughter2(); ++child) {
    children.push_back(&event[child]);
  }
  return children;
}


/**
 * @brief Get all descendants from a given particle. Iterates through all the
 * generation of children, until they are all final state (status > 0).
 *
 * @param event [description]
 * @param p Particle to get descendants.
 * @param finalStateOnly If true, returns only descendants which are final state
 * (status > 0). Otherwise, returns all intermediate children as well.
 * @return Returns a vector of Particle*
 */
std::vector<Particle*> getAllDescendants(Event & event, Particle * p, bool finalStateOnly) {
  bool allFinalState = false;
  std::vector<Particle*> intermediates = {p}; // hold the intermediates
  std::vector<Particle*> descendants; // hold all the particles to be returned
  while (!allFinalState) {
    allFinalState = true;
    std::vector<Particle*> newIntermediates;
    for (auto & pItr : intermediates) {

      if (pItr->isFinal()) continue;

      auto kids = getChildren(event, pItr);
      for (auto & childItr : kids) {
        if (finalStateOnly) {
          if (childItr->isFinal()) {
            descendants.push_back(childItr);
          }
        } else {
          descendants.push_back(childItr);
        }
        allFinalState = allFinalState && childItr->isFinal();
      }
      newIntermediates.insert(newIntermediates.end(), kids.begin(), kids.end());
    }
    intermediates = newIntermediates;
    newIntermediates.clear(); // prob don't need this, but at least explicit
  }
  return descendants;
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