#NMSSMPheno

For NMSSM phenomenology studies.

Basic overview:

1) Make MC complete with showering using Pythia8 (for signal processes) or MG5_aMC@NLO (for SM processes).

2) Run through Delphes for a detector simulation based around CMS (TODO)

3) Analyse with MadAnlaysis (TODO)

This system has been designed to run on the 2 batch systems:
- HTCondor system at Bristol (Advice: do it inside of `CMSSW_7_4_4_ROOT5` environment to avoid compiler horror)
- PBS-based systems, for use at Soton

##Installation

- Clone this repository:

```
git clone git@github.com:raggleton/NMSSMPheno.git
```

- Follow the program installation instructions for the batch system you are using:
    - HTCondor (Soolin @ Bristol): [INSTALL_CONDOR.md](INSTALL_CONDOR.md)
    - PBS (Soton / Bluecrystal @ Bristol): [INSTALL_PBS.md](INSTALL_PBS.md)
