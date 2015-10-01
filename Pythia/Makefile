# Makefile for compiling Pythia programs with necessary linking to libraries
# Compile programs using e.g. `make generateMC`

# Automatically handles different systems (e.g. using CMSSW on soolin)
# The user should check the location of the various programs.

SHELL = /bin/sh
CXX = g++

# Location of usual subdirectories
# -------------------------------------------------
INCDIR = include
SRCDIR = src
LIBDIR = lib
LIBDIRARCH = lib/archive
BINDIR = bin

# Set location of programs depending on system
# -------------------------------------------------

# For IRIDIS:
ifneq ($(findstring cyan, $(shell hostname)), )
	PYTHIA8DIR = $(HOME)/Pythia8/pythia8212
	FASTJETDIR = $(HOME)/fastjet-install
	HEPMCDIR = $(HOME)/HepMC/install
	ROOTDIR = $(HOME)/root5_install
	BOOSTDIR = /local/software/boost/1.54.0/
	BOOSTDIR_INC = $(BOOSTDIR)/$(INCDIR)
	BOOSTDIR_LIB = $(BOOSTDIR)/$(LIBDIR)
# For SOOLIN:
# Currently setup for use on soolin, within CMSSW_7_4_4_ROOT5
# It took a *LOT* of work to find all the compatible releases/compiler...
# Change at your own peril!
else ifneq ($(findstring soolin, $(shell hostname)), )
	PYTHIA8DIR = $(HOME)/pythia8209
	FASTJETDIR = $(HOME)/fastjet-install
	# Don't call it HEPMCDIR beacuse it defaults to /build/degano not cvmsfs within cmssw for some stupid reason
	HEPMCDIR = $(HOME)/HepMC/install
	ROOTDIR = /cvmfs/cms.cern.ch/slc6_amd64_gcc491/lcg/root/5.34.22-ilphmn/
	BOOSTDIR_INC = /cvmfs/cms.cern.ch/slc6_amd64_gcc491/external/boost/1.57.0-cms/include/
	BOOSTDIR_LIB = /cvmfs/cms.cern.ch/slc6_amd64_gcc491/cms/cmssw/CMSSW_7_4_4_ROOT5/external/slc6_amd64_gcc491/lib
else
$(error No rules for the hostname $(shell hostname).)
endif

# DON'T EDIT ANYTHING BELOW HERE

# Other common flags
# -------------------------------------------------
CXX_COMMON = -std=c++11 -pthread -D_USE_XOPEN2K8 -Wall -Wextra -Wshadow -pedantic-errors

# `$(FASTJETDIR)/bin/fastjet-config --cxxflags --plugins` \
# `$(FASTJETDIR)/bin/fastjet-config --libs --plugins` \

# Make using e.g. make generateMC
# For pythia 8.2X
.cc:
	$(CXX) $@.cc $(PYTHIA8DIR)/$(LIBDIR)/libpythia8.a -o $@.exe \
	-w -I$(ROOTDIR)/$(INCDIR) \
	-I$(BOOSTDIR_INC) \
	-I$(HEPMCDIR)/$(INCDIR) \
	-I$(PYTHIA8DIR)/$(INCDIR) \
	$(CXX_COMMON) \
	-I./ -L./ -Wl,-rpath ./ -lz -Wl,-rpath $(PYTHIA8DIR)/$(LIBDIR) -ldl \
	-L$(BOOSTDIR_LIB) -lboost_system -lboost_filesystem -lboost_program_options -lboost_iostreams -Wl,-rpath $(BOOSTDIR_LIB) \
	-L$(HEPMCDIR)/$(LIBDIR) -Wl,-rpath $(HEPMCDIR)/$(LIBDIR) -lHepMC \
	-Wl,-rpath $(ROOTDIR)/$(LIBDIR) `$(ROOTDIR)/$(BINDIR)/root-config --glibs` \


# Clean up: remove executables and outdated files.
.PHONY: clean
clean:
	rm *.exe
