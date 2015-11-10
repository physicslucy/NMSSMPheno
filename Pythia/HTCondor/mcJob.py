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

    # tar up output
    hepmc_file = get_option_in_args(args.args, '--hepmc')
    lhe_file = get_option_in_args(args.args, '--lhe')

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


def get_option_in_args(args, flag):
    """Return value that accompanied flag in list of args.

    Will return None if there is no accompanying value, and will raise a
    KeyError if the flag does not appear in the list.

    >>> args = ['--foo', 'bar', '--man']
    >>> get_option_in_args(args, "--foo")
    bar
    >>> get_option_in_args(args, "--man")
    None
    >>> get_option_in_args(args, "--fish")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "submit_mc_jobs_htcondor.py", line 272, in get_option_in_args
        raise KeyError('%s not in args' % flag)
    KeyError: '--fish not in args'
    """
    # maybe a dict would be better for this and set_option_in_args()?
    if flag not in args:
        raise KeyError('%s not in args' % flag)
    if flag == args[-1]:
        return None
    val = args[args.index(flag) + 1]
    if val.startswith('-'):
        return None
    return val


if __name__ == "__main__":
    main()
