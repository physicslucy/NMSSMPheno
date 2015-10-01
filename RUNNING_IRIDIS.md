#RUNNING_IRIDIS

Instructions for running the complete chain on Iridis, using the PBS batch system.

There are a few steps:

1) Generate Monte Carlo events for signal or SM processes

2) Apply detector simulation

3) Analyse it all

##Generate Monte Carlo

SM processes are generated with MadGraph5_aMC@NLO, whilst SUSY processes are generated with Pythia8. There are slightly different instructions for each.

###Standard Model: MG5_aMC@NLO

To run MG5_aMC we pass it an input card specifying the SM process and any other options. See [input_cards](MG5_aMC/input_cards).

For example:

```
blah blah blah
```

**TODO**

####Running on PBS batch system

**TODO**

###SUSY: Pythia8

One program is responsible for running Pythia8, [generateMC.cc](Pythia/generateMC.cc). The exact process(es) are specified using an input card, see [input_cards](Pythia/input_cards). Common options (e.g. beam parameters) are specified in [common_pp13.cmnd](Pythia/input_cards/common_pp13.cmnd). If one wishes to analyse the event (e.g. save a distribution to a ROOT file), one should edit [generateMC.cc](Pythia/generateMC.cc) directly.

Compile the program using

```
make generateMC
```

Run it interactively using

```
./generateMC.exe <opts>
```

To see possible options use the `--help` flag. At a minimum, you will want to specify the card file, the mass of the lightest boson, and the output format. We use the HepMC format to store the complete event, including hadronisation.

####Running on PBS batch system

**TODO**

##Apply detector simulation

Detector simulation is applied using Delphes. We pass it a HepMC file as generated in the previous step, and a card specifying the detector configuration.

For example:

```
./DelphesHEPMC
```

**TODO**

####Running on PBS batch system

**TODO**

##Analysis

**TODO**