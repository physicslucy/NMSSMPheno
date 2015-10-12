#RUNNING_IRIDIS

Instructions for running the complete chain on Soolin, using the HTCondor batch system.

There are a few steps:

1) Generate Monte Carlo events for signal or SM processes

2) Apply detector simulation

3) Analyse it all

##Generate Monte Carlo

SM processes are generated with MadGraph5_aMC@NLO, whilst SUSY processes are generated with Pythia8. There are slightly different instructions for each.

###Standard Model: MG5_aMC@NLO

**TODO**

####Running batch jobs

**TODO**

###SUSY: Pythia8

One program is responsible for running Pythia8, [generateMC.cc](Pythia/src/generateMC.cc). The exact process(es) are specified using an input card, see [input_cards](Pythia/input_cards). Common options (e.g. beam parameters) are specified in [common_pp13.cmnd](Pythia/input_cards/common_pp13.cmnd).

To compile and produce the executable:

```
cd Pythia
make
```

Then to run it:

```
./generateMC.exe <opts>
```

See a list of options by using the `--help` flag. **As a minimum** you will need the name of an input card. There are also options for changing the number of events to generate, changing the mass of the a1, as well as several output formats. They all take optional filenames. If no filename is specified, then one will be auto-generated based upon the input card, mass, and random number generator seed.

- `--hepmc`: saves the **complete event listing (including hadronisation)** in HepMC format. Suitable for passing to Delphes.
- `--lhe`: saves the **hard process only** in LHE format. Suitable for passing to another MC program to hadronise, or to study the hard event itself.
- `--root`: saves user-defined histograms to a ROOT file. The user must define the histogram objects, and can then fill them by analysing the Pythia event object. This is done in [generateMC.cc](Pythia/src/generateMC.cc).

####Running batch jobs

**TODO**

##Apply detector simulation

Detector simulation is applied using Delphes. We pass it a HepMC file as generated in the previous step, and a card specifying the detector configuration.

For example:

```
./DelphesHEPMC
```

**TODO**

###Running batch jobs

**TODO**

##Analysis

**TODO**

###Running batch jobs

**TODO**