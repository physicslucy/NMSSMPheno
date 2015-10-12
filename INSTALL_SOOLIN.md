#Installation instruction for running on Soolin at Bristol

- [MG5_aMC@NLO (background MC)](#mg5_amcnlo-background-mc)
- [Pythia8 (signal MC)](#pythia8-signal-mc)
- [Delphes (detector simulation)](#delphes-detector-simulation)
- [MadAnalysis (analysis)](#madanalysis-analysis)

**VERY IMPORTANT**: do all of this inside the CMSSW_7_4_4_ROOT5 release. It has all the correct GCC, ROOT, etc setup:

```
cmsrel CMSSW_7_4_4_ROOT5
```

##MG5_aMC@NLO (background MC)

Download tar into $HOME/zips.
Extract, and test it runs OK interactively.

##Pythia8 (signal MC)

First install:

- HepMC
- FastJet
- LHAPDF6

BOOST and ROOT5 are also required, but can use central installations instead.

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

Test the libraries have compiled fine by compiling & running example programs:

```
cd examples
make mainXX
./mainXX
```

- `main01`: very basic, no dependencies
- `main41`: test HepMC linked correctly
- `main52`: test LHAPDF linked correctly. Note that this example still uses LHAPDF5, so you will need to manually change:

```
string pdfSet = "LHAPDF5:MRST2001lo.LHgrid";
\\ change to
string pdfSet = "LHAPDF6:CT10nlo.LHgrid";
```

You should see when running:

```
LHAPDF 6.1.5 loading /users/ra12451/LHAPDF6-install/share/LHAPDF/CT10nlo/CT10nlo_0000.dat
CT10nlo PDF set, member #0, version 4; LHAPDF ID = 11000
```

- `main91`: test ROOT linked correctly


##Delphes (detector simulation)

Assumes ROOT5 already installed.

```
git clone git@github.com:delphes/delphes.git
cd delphes
make -j4
```

##MadAnalysis (analysis)

Download tar.