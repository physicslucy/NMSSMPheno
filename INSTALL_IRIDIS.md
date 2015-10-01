#Installation instruction for running on Iridis (Southampton)

- [MG5_aMC@NLO (background MC)](#mg5_amcnlo-background-mc)
- [Pythia8 (signal MC)](#pythia8-signal-mc)
  - [HepMC](#hepmc)
  - [BOOST](#boost)
  - [LHAPDF6](#lhapdf6)
  - [ROOT](#root)
  - [Pythia 8](#pythia-8)
- [Delphes (detector simulation)](#delphes-detector-simulation)
- [Random notes](#random-notes)

Load the following modules:

```
module load python
module load gcc/4.9.1
module load boost
module load cmake
module load gmake
module load gsl
module unload intel
```

Would also advise adding these automatically when logging in by using `module initadd <module>`.

Note that we unload the intel module as there are licensing issues that cause havok when compiling.

##MG5_aMC@NLO (background MC)

```
mkdir MG5_aMC
cd MG5_aMC
wget https://launchpad.net/mg5amcnlo/2.0/2.3.0/+download/MG5_aMC_v2.3.2.2.tar.gz -O- | tar xvz
```
Extract, and test it runs OK interactively.

##Pythia8 (signal MC)

First install:

- HepMC
- BOOST
- LHAPDF6
- ROOT

**TODO: fastjet**

###HepMC

```
wget http://lcgapp.cern.ch/project/simu/HepMC/download/HepMC-2.06.09.tar.gz -O- | tar xvz
mkdir -P HepMC/build HepMC/install
cd HepMC/build
../../HepMC-2.06.09/configure --prefix=${PWD}/../install/ --with-momentum=GEV --with-length=MM
make -j4
make check
make install
```

###BOOST

This is included in the list of activated modules above. Location of files can be found using `module show boost`.

###LHAPDF6

```
wget http://www.hepforge.org/archive/lhapdf/LHAPDF-6.1.5.tar.gz -O- | tar xvz
mkdir LHAPDF6
cd LHAPDF-6.1.5
./configure --prefix=${PWD}/../LHAPDF6
make -j4
make install
```

Note that LHAPDF does not come with the PDF sets - they must be downloaded separately. For example, to add the CT10NLO PDF:

```
 wget http://www.hepforge.org/archive/lhapdf/pdfsets/6.1/CT10nlo.tar.gz -O- | tar xz -C $HOME/LHAPDF6/share/LHAPDF
```

###ROOT

First we need to grab the Xpm graphic library, as although the shared library is available on Iridis, the header file isn't:

```
wget http://ftp.x.org/pub/individual/lib/libXpm-3.5.11.tar.gz -O- | tar xvz
```

To find the library file:

```
ldconfig -p | grep -i xpm
#     libXpm.so.4 (libc6,x86-64) => /usr/lib64/libXpm.so.4
```

Now we can try and compile ROOT, telling it to use the correct compilers (as the Intel ones have expired and CMake doesn't pick up our new modules), the correct Xpm library, and other customisations for ROOT (roofit and minuit fitter):

**Note that Pythia8 and Delphes both require ROOT5, whilst analysis should preferably use ROOT6. The instructions that follow are for ROOT5, but the same instructions work for both, changing `root5` to `root6` and the git tag.**

```
git clone http://root.cern.ch/git/root.git root5
cd root5
# git checkout -b v6-05-02 v6-05-02
git checkout -b v5-34-32 v5-34-32
mkdir ../root5_build ../root5_install
cd ../root5_build
cmake -G "Unix Makefiles" -DCMAKE_C_COMPILER=/local/software/gcc/4.9.1/bin/gcc \
-DCMAKE_CXX_COMPILER=/local/software/gcc/4.9.1/bin/g++ \
-DCMAKE_Fortran_COMPILER=/local/software/gcc/4.9.1/bin/gfortran \
-DX11_Xpm_INCLUDE_PATH:PATH=$HOME/libXpm-3.5.11/include/ \
-DX11_Xpm_LIB:FILEPATH=/usr/lib64/libXpm.so.4 \
-Droofit:BOOL=ON -Dminuit2:BOOL=ON $PWD/../root5/
nice -n 19 time cmake --build .
cmake -DCMAKE_INSTALL_PREFIX=$PWD/../root5_install -P cmake_install.cmake
source ../root5_install/bin/thisroot.sh
echo "source $PWD/../root5_install/bin/thisroot.sh" >> ~/.bash_profile
```

Note that building takes a very long time - about 3 hours for ROOT6, and about 1.5 hours for ROOT5.

Note to self: use `cmake -LAH` to list all CMake variables


###Pythia 8

```
mkdir Pythia8
wget http://home.thep.lu.se/~torbjorn/pythia8/pythia8212.tgz -O- | tar xvz -C Pythia8
cd Pythia8/pythia8212
./configure --with-hepmc2=$PWD/../../HepMC/install/ \
--with-boost=/local/software/boost/1.54.0/ \
--with-lhapdf6=$PWD/../../LHAPDF6/ \
--with-lhapdf6-plugin=$PWD/include/Pythia8Plugins/LHAPDF6.h \
--with-root=$PWD/../../root5_install/
make -j4
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
LHAPDF 6.1.5 loading /home/rca1e13/LHAPDF-6.1.5/../LHAPDF6/share/LHAPDF/CT10nlo/CT10nlo_0000.dat
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

##MadAnalysis (analysis framework)

**TODO**

##Random notes

----------------------------------------------------------------------
Libraries have been installed in:
   /home/rca1e13/root_build/lib

If you ever happen to want to link against installed libraries
in a given directory, LIBDIR, you must either use libtool, and
specify the full pathname of the library, or use the '-LLIBDIR'
flag during linking and do at least one of the following:
   - add LIBDIR to the 'LD_LIBRARY_PATH' environment variable
     during execution
   - add LIBDIR to the 'LD_RUN_PATH' environment variable
     during linking
   - use the '-Wl,-rpath -Wl,LIBDIR' linker flag
   - have your system administrator add LIBDIR to '/etc/ld.so.conf'

See any operating system documentation about shared libraries for
more information, such as the ld(1) and ld.so(8) manual pages.