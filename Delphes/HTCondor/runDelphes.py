#!/usr/bin/env python
"""
This script is designed to setup and run Delphes on the worker node on HTCondor.
User should not run this script directly!

This is mainly responsible for:

- setting up environment, programs
- copying necessary inputs from hdfs, renaming if necessary
- running program
- copying various outputs to hdfs, renaming if necessary
"""

import os
import argparse
import sys
import shutil
from subprocess import call
import tarfile


def runDelphes(in_args=sys.argv[1:]):
    """Main routine"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--copyToLocal", nargs=2, action='append',
                        help="Files to copy to local area on worker node "
                        "before running program. "
                        "Must be of the form <source> <destination>. "
                        "Repeat for each file you want to copy.")
    parser.add_argument("--copyFromLocal", nargs=2, action='append',
                        help="Files to copy from local area on worker node "
                        "after running program. "
                        "Must be of the form <source> <destination>. "
                        "Repeat for each file you want to copy."
                        "Note that the output of Delphes files is set by "
                        "--process and should not be included here")
    parser.add_argument('--exe',
                        help="Delphes executable to run. "
                        "If not specified, it'll try and guess")
    parser.add_argument('--card', required=True,
                        help='Delphes card')
    parser.add_argument('--process', nargs=2, action='append',
                        help='File for Delphes to process, of the form: '
                        '<input file> <output file>')

    args = parser.parse_args(args=in_args)
    print args
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
            copy_to_local(source, dest)
        print os.listdir(os.getcwd())

    # Setup Delphes
    # -------------------------------------------------------------------------
    # assumes tarfile is called delphes.tgz!
    delphes_tar = 'delphes.tgz'
    call(['tar', 'xzf', delphes_tar])
    os.remove(delphes_tar)
    os.chdir('delphes')

    # Run Delphes over files
    # -------------------------------------------------------------------------
    for input_file, output_file in args.process:
        # To save disk space, we copy over a single file, process it,
        # then copy the result to its destination.
        in_local = os.path.basename(input_file)
        out_local = os.path.basename(output_file)

        copy_to_local(input_file, in_local)

        # unzip if necessary
        def need_unzip(filename):
            """Determine if file needs unzipping first"""
            f = os.path.basename(filename)
            return any([f.endswith(ext) for ext in ['.gz']])

        # eurgh this a bit horrific. really want some way to get the new filename
        if need_unzip(in_local):
            print 'Unzipping', in_local
            call(['gunzip', in_local])
        in_local = in_local.replace('.gz', '')

        def determine_exe(extension):
            if extension in ['.hepmc']:
                return './DelphesHepMC'
            elif extension in ['.lhe', '.lhef']:
                return './DelphesLHEF'
            else:
                raise RuntimeError('Cannot determine which exe to use for %s' % in_local)

        exe = args.exe if args.exe else determine_exe(os.path.splitext(in_local)[1])
        call([exe, os.path.join('..', args.card), out_local, in_local])

        copy_from_local(out_local, output_file)
        os.remove(out_local)
        os.remove(in_local)

    # Copy files from worker node area to /hdfs or /storage
    # -------------------------------------------------------------------------
    if args.copyFromLocal:
        for (source, dest) in args.copyFromLocal:
            print source, dest
            copy_from_local(source, dest)


def copy_to_local(source, dest):
    """Copy file from /hdfs, /storage, etc to local area."""
    if source.startswith('/hdfs'):
        source = source.replace('/hdfs', '')
        call(['hadoop', 'fs', '-copyToLocal', source, dest])
    else:
        if os.path.isfile(source):
            shutil.copy2(source, dest)
        elif os.path.isdir(source):
            shutil.copytree(source, dest)


def copy_from_local(source, dest):
    """Copy file from local area to e.g. /hdfs, /sorage, etc"""
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    if dest.startswith('/hdfs'):
        dest = dest.replace('/hdfs', '')
        call(['hadoop', 'fs', '-copyFromLocal', '-f', source, dest])
    else:
        if os.path.isfile(source):
            shutil.copy2(source, dest)
        elif os.path.isdir(source):
            shutil.copytree(source, dest)


if __name__ == "__main__":
    runDelphes()
