#!/bin/bash -e

# This script setups and run MG5_aMC on the worker node on HTCondor
# The user should NOT run this script directly!

card=""
nEvents=0
outputDir=""

while getopts ":c:n:o:" opt; do
    case $opt in
        \?)
            echo "Invalid option $OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
        c)
            echo "MG5_aMC@NLO Card filename: $OPTARG"
            card=$OPTARG
            ;;
        n)
            echo "Number of events to generate: $OPTARG"
            nEvents=$OPTARG
            ;;
        o)
            echo "Output directory: $OPTARG"
            outputDir=$OPTARG
            ;;
    esac
done

process="${card%.*}"
BASE=$PWD

#--------------------------------------------------------------------------
# Setup environment, software
#--------------------------------------------------------------------------
# Need to setup CMSSW_7_4_4 to get a decent GCC version that actually works.
export SCRAM_ARCH=slc6_amd64_gcc491
VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
. $VO_CMS_SW_DIR/cmsset_default.sh
scramv1 project CMSSW CMSSW_7_4_4_ROOT5
cd CMSSW_*/src/
eval `scramv1 runtime -sh`
cd ../..

# Setup HepMC2
# Use cvmfs one for now...
HEPMC_PATH=/cvmfs/sft.cern.ch/lcg/external/HepMC/2.06.08/x86_64-slc6-gcc48-opt/

# Now need to setup Pythia8 for showering
tar xvzf pythia8*.tgz
cd pythia8*
echo $PWD
./configure --with-hepmc2=$HEPMC_PATH
# ./configure --with-gzip --with-hepmc2=$HEPMC_PATH
make -j8
ls bin
cd ..

# Need to make sure it picks up correct libs and XML file
# since it uses PYTHIA8DATA var preferentially
export LD_LIBRARY_PATH=$HEPMC_PATH/lib:$LD_LIBRARY_PATH
export PYTHIA8DATA=$BASE/pythia8209/share/Pythia8/xmldoc

# Setup MG5_aMC
tar xvzf MG5_aMC_v*.tar.gz
ls
cd MG5_aMC_v2_*
echo $PWD

#--------------------------------------------------------------------------
# Running MG5_aMC@NLO
#--------------------------------------------------------------------------
# Edit the card to point to Pythia, and set correct number of events
# TODO: improve this
mv $BASE/$card .
if [ ! -e "$card" ]
then
    echo "Input card file $card does not exist!"
    exit 1
fi
sed -i s@/users/ra12451@${BASE}@ $card
sed -ie "s@set run_card nevents [0-9]*@set run_card nevents $nEvents@" $card

# Now generate some MC!
./bin/mg5_aMC "$card"

#--------------------------------------------------------------------------
# Move to output directory
#--------------------------------------------------------------------------
if [ ! -d "$outputDir" ]
then
    echo "Making output dir $outputDir"
    mkdir "$outputDir"
fi
echo "Moving output to $outputDir"

# needed as the output gets put in a dir determined
# by the line 'output XXX' in the card file
mgDir=`grep 'output'  ${card} | cut -d" " -f 2`
ls "$mgDir"/Events/
# add a unique append to the files, of the form _<date>_<time>_<random string>
dt=$(date '+%d_%m_%y_%H%M%S')
rand=$(cat /dev/urandom | tr -cd [:alnum:] | head -c 3)
for f in "$mgDir"/Events/run_*/events*; do
    newName=`basename "$f"`
    ext=${newName#*.}
    newName="${newName%%.*}_${dt}_${rand}"
    mv "$f" "$outputDir/${newName}.${ext}"
done
