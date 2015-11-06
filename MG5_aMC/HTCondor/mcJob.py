#!/bin/env python
"""
This script is designed to setup and run on the worker node on HTCondor.
User should not run this script directly!
"""


import argparse
from subprocess import call
import sys
import shutil
import os
import sys
import tarfile
from glob import glob


def main(in_args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copyToLocal", nargs=2, action='append',
                        help="Files to copy to local area on worker node "
                        "before running program. "
                        "Must be of the form <source> <destination>. "
                        "Repeat for each file you want to copy.")
    parser.add_argument("--copyFromLocal", nargs=2, action='append',
                        help="Files to copy from local area on worker node "
                        "after running program. "
                        "Must be of the form <source> <destination>. "
                        "Repeat for each file you want to copy.")
    parser.add_argument('--oDir', help='Output directory for HepMC/LHE files')
    parser.add_argument("--exe", help="Name of executable", default="mc.exe")
    parser.add_argument("--args", nargs=argparse.REMAINDER,
                        help="")
    args = parser.parse_args(args=in_args)
    print args
    print os.environ

    # Make sandbox area to avoid names clashing, and stop auto transfer
    # back to submission node
    # -------------------------------------------------------------------------
    os.mkdir('scratch')
    os.environ['SCRATCH'] = os.path.abspath('scratch')
    os.chdir('scratch')

    # Copy files to worker node area from /users, /hdfs, /storage, etc.
    # -------------------------------------------------------------------------
    if args.copyToLocal:
        for (source, dest) in args.copyToLocal:
            print source, dest
            if source.startswith('/hdfs'):
                source = source.replace('/hdfs', '')
                call(['hadoop', 'fs', '-copyToLocal', source, dest])
            else:
                if os.path.isfile(source):
                    shutil.copy2(source, dest)
                elif os.path.isdir(source):
                    shutil.copytree(source, dest)
        print os.listdir(os.getcwd())

    # TODO: move setups to spearate shell scripts?
    """
    # Do setup of CMSSW
    # -------------------------------------------------------------------------
    # Need to setup CMSSW_7_4_4_ROOT5 to get a decent GCC version that actually works.
    os.environ['SCRAM_ARCH'] = 'slc6_amd64_gcc491'
    os.environ['VO_CMS_SW_DIR'] = '/cvmfs/cms.cern.ch'
    # The shell=True is required as the cmsset_default.sh isn't a proper shell
    # script, no shebang, grrr
    call(['/cvmfs/cms.cern.ch/cmsset_default.sh'], shell=True)
    cmssw_ver = 'CMSSW_7_4_4_ROOT5'
    call(['scramv1', 'project', 'CMSSW', cmssw_ver])
    os.chdir('%s/src' % cmssw_ver)
    call('scramv1 runtime -sh'.split())
    os.chdir('../..')

    # Setup HepMC
    # -------------------------------------------------------------------------
    # Use cvmfs one for now...
    hepmc_path = '/cvmfs/sft.cern.ch/lcg/external/HepMC/2.06.08/x86_64-slc6-gcc48-opt/'
    os.environ['HEPMC_PATH'] = hepmc_path

    # Setup Pythia8 for showering
    # -------------------------------------------------------------------------
    pythia_tar = glob('pythia8.tgz')
    if len(pythia_tar) > 1:
        raise RuntimeError('Ambiguous Pythia8 tarball file')
    elif len(pythia_tar) == 0:
        raise RuntimeError('No Pythia tarball')
    pythia_tar = pythia_tar[0]
    with tarfile.open(pythia_tar) as tar:
        tar.extractall()
    os.remove(pythia_tar)
    pythia_path = os.path.abspath(glob('pythia8*')[0])
    os.chdir(pythia_path)
    call(['./configure', '--with-hepmc2=%s' % hepmc_path])
    call(['make'])
    os.listdir('.')
    os.chdir('..')

    os.environ['LD_LIBRARY_PATH'] = '%s:%s' % (os.environ['HEPMC_PATH'], os.environ['LD_LIBRARY_PATH'])
    os.environ['PYTHIA8DATA'] = '%s/pythia8209/share/Pythia8/xmldoc' % pythia_path
    """
    # Setup MG5_aMC
    # -------------------------------------------------------------------------
    mg5_tar = glob('MG5_aMC*.tgz')
    if len(mg5_tar) > 1:
        raise RuntimeError('Ambiguous MG5 tarball file')
    elif len(mg5_tar) == 0:
        raise RuntimeError('No MG5 tarball')
    mg5_tar = mg5_tar[0]
    with tarfile.open(mg5_tar) as tar:
        tar.extractall()
    os.remove(mg5_tar)
    mg5_dir = glob('MG5_aMC_v*')[0]

    print os.environ['LD_LIBRARY_PATH']

    # Run the program
    # -------------------------------------------------------------------------
    mg5_args = args.args
    mg5_args.extend(['--exe', os.path.join(mg5_dir, 'bin', 'mg5_aMC')])
    # mg5_args.extend(['--pythia8', pythia_path])
    # mg5_args.extend(['--hepmc', hepmc_path])
    print mg5_args

    sys.path.insert(0, os.path.abspath('.'))
    import run_mg5
    run_args = run_mg5.run_mg5(mg5_args)
    print run_args

    # Get the value of the several variables from the card
    # -------------------------------------------------------------------------
    mg5_out_dir = get_value_from_card(run_args.new_card, 'output')
    iseed = int(get_value_from_card(run_args.new_card, 'iseed'))
    energy = int(get_value_from_card(run_args.new_card, 'ebeam1')) * 2/1000
    num_events = int(get_value_from_card(run_args.new_card, 'nevents'))

    # Deal with output file
    # -------------------------------------------------------------------------
    os.chdir(os.path.join(mg5_out_dir, 'Events', 'run_01'))
    # Rename gzipped files to use iseed
    card = os.path.basename(run_args.card)
    name_stem = '%s_%dTeV_n%d_seed%d' % (mg5_out_dir, energy, num_events, iseed)
    print name_stem

    lhe_zip = '%s.lhe.gz' % name_stem
    os.rename('events.lhe.gz', lhe_zip)
    lhe_path = os.path.abspath(lhe_zip)

    hepmc_zip = '%s.hepmc.gz' % name_stem
    os.rename('events_PYTHIA8_0.hepmc.gz', hepmc_zip)
    hepmc_path = os.path.abspath(hepmc_zip)

    # Unzip them...? Keep compressed, for now
    # call(['gunzip', lhe_zip])
    # call(['gunzip', hepmc_zip])

    # Add the HepMC and LHE gzip to copyFromLocal queue
    # -------------------------------------------------------------------------
    if not args.copyFromLocal:
        args.copyFromLocal = []
    args.copyFromLocal.append([lhe_path, os.path.join(args.oDir, 'lhe', lhe_zip)])
    args.copyFromLocal.append([hepmc_path, os.path.join(args.oDir, 'hepmc', hepmc_zip)])

    print args.copyFromLocal

    # Copy files from worker node area to /hdfs or /storage
    # -------------------------------------------------------------------------
    if args.copyFromLocal:
        for (source, dest) in args.copyFromLocal:
            print source, dest
            check_create_dir(dest)
            if dest.startswith('/hdfs'):
                dest = dest.replace('/hdfs', '')
                call(['hadoop', 'fs', '-copyFromLocal', '-f', source, dest])
            else:
                if os.path.isfile(source):
                    shutil.copy2(source, dest)
                elif os.path.isdir(source):
                    shutil.copytree(source, dest)


def check_create_dir(directory, info=False):
    """Check dir exists, if not create"""
    if not os.path.isdir(directory):
        if os.path.isfile(directory):
            raise RuntimeError('%s already exists as a file' % directory)
        os.makedirs(directory)
        if info:
            print 'Making dir', directory


def get_value_from_card(card, field):
    """Get value of field from card.

    card: str
        Filename
    field: str
        Field name
    """
    with open(card) as f:
        for line in f:
            if field in line.strip():
                return line.strip().split()[-1]


if __name__ == "__main__":
    main()
