#!/usr/bin/env python
"""
Submit lots of Pythia8 jobs to condor. All jobs run using the same input card.

The user should specify the Pythia executable, an input card with physics
processes & other instructions for Pythia8, an output directory on /hdfs,
the number of events to generate per job, and the number of jobs to submit.
There is also the option for a 'dry run' where all the files & directories are
set up, but the job is not submitted.

Note that this submits the jobs not one-by-one but as a DAG, to allow easier
monitoring of job status.
"""


import shutil
from time import strftime
from subprocess import call
import argparse
import sys
import os
import getpass
import logging


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def submit_mc_jobs_htcondor(in_args=sys.argv[1:]):
    """
    Main function. Sets up all the relevant directories, makes condor
    job and DAG files, then submits them if necessary.
    """

    # Handle user options. The user can pass all the same options as they
    # would if running the program locally. However, for certain options,
    # we interecpt the argument(s) and modify if necessary.
    parser = argparse.ArgumentParser(description=__doc__)

    # Options for the job submitter
    parser.add_argument("jobIdRange",
                        help="Specify job ID range to run over. The ID is used"
                        " as the random number generator seed, so manual "
                        "control is needed to avoid making the same files."
                        "Must be of the form: startID, endID. ",
                        nargs=2, type=int)
    parser.add_argument("--oDir",
                        help="Directory for output HepMC files. "
                        "If no directory is specified, an automatic one will "
                        "be created at: "
                        "/scratch/<username>/NMSSMPheno/Pythia8/<card>/<date>",
                        default="")
    parser.add_argument("--exe",
                        help="Executable to run.",
                        default="generateMC.exe")
    # parser.add_argument("--massRange",
    #                     help="Specify mass range to run over. "
    #                     "Must be of the form: startMass, endMass, massGap. "
    #                     "For each mass point, njobs jobs will be submitted.",
    #                     nargs=3, type=float)
    # All other program arguments to pass to program directly.
    parser.add_argument("--args",
                        help="All other program arguments. "
                        "You must specify this after all other options",
                        nargs=argparse.REMAINDER)
    # Some generic script options
    parser.add_argument("--dry",
                        help="Dry run, don't submit to queue.",
                        action='store_true')
    parser.add_argument("-v",
                        help="Display debug messages.",
                        action='store_true')
    args = parser.parse_args(args=in_args)

    if args.v:
        logging.setLevel(logging.DEBUG)

    log.debug(args)

    # Do some checks
    # -------------------------------------------------------------------------
    if not os.path.isfile(args.exe):
        raise RuntimeError('Executable %s does not exist' % args.exe)

    # Get the input card from user's options & check it exists
    card = get_option_in_args(args.args, "--card")
    if not os.path.isfile(card):
        raise RuntimeError('Input card %s does not exist!' % card)
    channel = os.path.splitext(os.path.basename(card))[0]

    # Auto generate output directory if necessary
    # -------------------------------------------------------------------------
    if args.oDir == "":
        args.oDir = generate_dir_soolin(channel)

    checkCreateDir(args.oDir, args.v)

    # Setup log directory
    # -------------------------------------------------------------------------
    log_dir = '%s/logs' % generate_subdir(channel)
    checkCreateDir(log_dir, args.v)

    # Copy executable to outputdir to sandbox it
    # -------------------------------------------------------------------------
    sandbox_exe = os.path.join(args.oDir, os.path.basename(args.exe))
    shutil.copy2(args.exe, sandbox_exe)

    # File stem common for all condor, dag, status files
    # -------------------------------------------------------------------------
    mass = get_option_in_args(args.args, '--mass')
    file_stem = '%s/ma%s_%s' % (generate_subdir(channel),
                                         mass, strftime("%H%M%S"))
    checkCreateDir(os.path.dirname(file_stem), args.v)

    # Make a condor job file for this batch using the template
    script_name = file_stem + '.condor'
    write_condor_file(condor_filename=script_name,
                      log_dir=log_dir, log_file='$(JOB)')

    # Make DAG file
    # -------------------------------------------------------------------------
    dag_name = file_stem + '.dag'
    status_name = file_stem + '.status'
    write_dag_file(dag_filename=dag_name, condor_filename=script_name,
                   status_filename=status_name, exe=sandbox_exe,
                   channel=channel, mass=mass, args=args)

    # Submit it
    # -------------------------------------------------------------------------
    if not args.dry:
        call(['condor_submit_dag', dag_name])
        log.info('Check status with:')
        log.info('DAGstatus.py %s' % status_name)
        print ''
        log.info('Condor log files written to: %s' % log_dir)


def write_condor_file(condor_filename, log_dir, log_file):
    """Write condor job file using a template.

    log_dir: str
        Directory for log files
    log_file: str
        Filename stem for log files. Note that the complete log filename will
        be $(cluster).$(process).<log_file>.[out|err|log]
    condor_filename: str
        Name of condor job file to be produced
    """
    with open('HTCondor/mcJob.condor', 'r') as template:
        job_template = template.read()

    job_description = job_template.replace('SEDLOGDIR', log_dir)
    job_description = job_description.replace('SEDLOGFILE', log_file)

    log.info('Condor job file: %s', condor_filename)
    with open(condor_filename, 'w') as job_file:
        job_file.write(job_description)


def write_dag_file(dag_filename, condor_filename, status_filename,
                   exe, channel, mass, args):
    """Write a DAG file for a set of jobs.

    Creates a DAG file, adding extra flags for the worker node script.
    This includes setting the random number generator seed, and copying files
    to & from /hdfs. Also ensures a DAG status file will be written every 30s.

    dag_filename: str
        Name to be used for DAG job file.
    condor_filename: str
        Name of condor job file to be used for each job
    status_filename: str
        Name to be used for DAG status file.
    exe: str
        Location of sandboxed executable to copy accross
    channel: str
        Name of channel. Used to auto-generate HepMC filename.
    mass: str
        Mass of a1 boson. Used to auto-generate HepMC filename.
    args: argparse.Namespace
        Contains info about output directory, job IDs, number of events per job,
        and args to pass to the executable.
    """
    # get number of events to generate
    if '--number' in args.args:
        n_events = get_option_in_args(args.args, "--number")
    elif '-n' in args.args:
        n_events = get_option_in_args(args.args, "-n")
    else:
        log.warning('Number of events not specified - assuming 1')
        n_events = 1

    log.info("DAG file: %s" % dag_filename)
    with open(dag_filename, 'w') as dag_file:
        dag_file.write('# DAG for channel %s\n' % channel)
        dag_file.write('# Outputting to %s\n' % args.oDir)
        for job_ind in xrange(args.jobIdRange[0], args.jobIdRange[1] + 1):
            job_name = '%d_%s' % (job_ind, channel)
            dag_file.write('JOB %s %s\n' % (job_name, condor_filename))
            exe_args = args.args[:]

            # Auto generate output filename if necessary
            if "--hepmc" not in exe_args:
                hepmc_name = "%s_ma1_%s_%s.hepmc" % (channel, mass, n_events)
                exe_args.extend(['--hepmc', hepmc_name])

            # Use the filename itself, ignore any directories from user.
            hepmc_name = os.path.basename(get_option_in_args(exe_args, "--hepmc"))

            # Add in seed/job ID to filename.
            hepmc_name = "%s_%d.hepmc" % (os.path.splitext(hepmc_name)[0], job_ind)
            set_option_in_args(exe_args, "--hepmc", hepmc_name)

            remote_exe = 'mc.exe'
            job_opts = ['--copyToLocal', os.path.abspath('input_cards'), 'input_cards',
                        '--copyToLocal', exe, remote_exe,
                        '--exe', remote_exe,
                        '--copyFromLocal', hepmc_name, args.oDir,
                        '--args']

            # Add in RNG seed based on job index
            exe_args.extend(['--seed', str(job_ind)])
            job_opts.extend(exe_args)
            dag_file.write('VARS %s opts="%s"\n' % (job_name, ' '.join(job_opts)))
        dag_file.write('NODE_STATUS_FILE %s 30\n' % status_filename)


def checkCreateDir(directory, info=False):
    """Check to see if directory exists, if not make it.

    Can optionally display message to user.
    """
    if not os.path.isdir(directory):
        if os.path.isfile(directory):
            raise RuntimeError("Cannot create directory %s, already "
                               "exists as a file object" % directory)
        os.makedirs(directory)
        if info:
            print "Making dir %s" % directory


def generate_subdir(channel):
    """Generate a subdirectory name using channel and date.
    Can be used for output and log files, so consistent between both.

    >>> generate_subdir('ggh_4tau')
    ggh_4tau/05_Oct_15
    """
    return os.path.join(channel, strftime("%d_%b_%y"))


def generate_dir_soolin(channel):
    """Generate a directory name on Iridis using userId, channel, and date.

    >>> generate_dir_iridis('ggh_4tau')
    /hdfs/user/<username>/NMSSMPheno/Pythia8/ggh_4tau/<date>
    """
    uid = getpass.getuser()
    return "/hdfs/user/%s/NMSSMPheno/Pythia8/%s" % (uid, generate_subdir(channel))


def get_option_in_args(args, flag):
    """Return value that accompanied flag in list of args.

    >>> args = ['--foo', 'bar', '--man', 'bear']
    >>> get_option_in_args(args, "--foo")
    bar
    """
    if flag not in args:
        raise KeyError('%s not in args' % flag)
    return args[args.index(flag) + 1]


def set_option_in_args(args, flag, value):
    """Set value for flag in list of args.

    >>> args = ['--foo', 'bar', '--man', 'bear']
    >>> set_option_in_args(args, '--foo', 'ball')
    >>> args
    ['--foo', 'ball', '--man', 'bear']
    """
    args[args.index(flag) + 1] = value


if __name__ == "__main__":
    submit_mc_jobs_htcondor()
