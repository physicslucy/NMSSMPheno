#Installation instruction for running on Soolin at Bristol


##MG5_aMC@NLO (background MC)

Download tar into $HOME/zips.
Extract, and test it runs OK interactively.

##Pythia8 (signal MC)

First install:

- HepMC
- FastJet
- LHAPDF6

BOOST and ROOT are also required, but can use central installations instead.

Download Py8 tar into $HOME/zips.
Extract, and test it compiles OK (not actually needed for running jobs).
Will need compile flags:

```
./configure --with-hepmc2=/users/ra12451/HepMC/install/ --with-fastjet3=/users/ra12451/fastjet-install --with-boost-include=/cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/boost/1.57.0-cms/include/ --with-boost-lib=/cvmfs/cms.cern.ch/slc6_amd64_gcc491/cms/cmssw/CMSSW_7_4_4_ROOT5/external/slc6_amd64_gcc491/lib --with-gzip-bin=/bin/gzip --cxx-common='-D__USE_XOPEN2K8 -fPIC' --with-lhapdf6=/users/ra12451/LHAPDF6-install/ --with-lhapdf6-plugin=include/Pythia8Plugins/LHAPDF6.h --with-root=/cvmfs/cms.cern.ch/slc6_amd64_gcc491/lcg/root/5.34.22-ilphmn/
```

Also need to set

```
export PYTHIA8DATA=/users/ra12451/pythia8209/share/Pythia8/xmldoc/
```
to avoid the error message:

```
PYTHIA Abort from Pythia::Pythia: unmatched version numbers : in code 8.209 but in XML 8.205
```

##Delphes (detector simulation)

Clone Delphes into home dir:

```
git clone git@github.com:delphes/delphes.git
```

##MadAnalysis (analysis)

Download tar.