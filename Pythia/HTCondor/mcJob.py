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
    parser.add_argument("--exe", help="Name of executable", default="mc.exe")
    parser.add_argument("--args", nargs=argparse.REMAINDER,
                        help="")
    args = parser.parse_args(args=in_args)
    print args

    # Make sandbox area to avoid names clashing, and stop auto transfer
    # back to submission node
    # -------------------------------------------------------------------------
    os.mkdir('scratch')
    os.chdir('scratch')

    # Copy files to worker node area from /users, /hdfs, /storage, etc.
    # -------------------------------------------------------------------------
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

    # Run the program
    # -------------------------------------------------------------------------
    os.chmod(args.exe, 0555)
    cmds = ["./" + args.exe] + args.args
    print cmds
    call(cmds)

    print os.listdir(os.getcwd())

    # Copy files from worker node area to /hdfs or /storage
    # -------------------------------------------------------------------------
    for (source, dest) in args.copyFromLocal:
        print source, dest
        if dest.startswith('/hdfs'):
            dest = dest.replace('/hdfs', '')
            call(['hadoop', 'fs', '-copyFromLocal', '-f', source, dest])
        else:
            if os.path.isfile(source):
                shutil.copy2(source, dest)
            elif os.path.isdir(source):
                shutil.copytree(source, dest)


if __name__ == "__main__":
    main()
