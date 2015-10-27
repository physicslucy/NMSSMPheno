#!/bin/env python

"""
This script submits MC generation jobs to a PBS batch system.

The user must specify the range of job IDs to submit. The job ID also sets the
random number generator seed, thus one should avoid using the same job ID more
than once. The user can also specify the output directory
(or one will be auto-generated), as well as a custom executable. There is also
the possibiility of looping over a range of masses, in which case job IDs
(as specified the jobIdRange arguments) will be used for each mass.

To pass arguments to the Pythia8 program, use the '--args' flag.
e.g. if you ran locally with:
'--card mycard.txt --mass 8 -n 10000'
you should call this script with:
'--args --card mycard.txt --mass 8 -n 10000'

Note that --args must be specified after all other arguments!

There is also the option for a 'dry run' where all the files & directories are
set up, but the job is not submitted.

The jobs are submitted as a "job array", to allow easier monitoring/handling of
the potentially large number of jobs.

"""


import os
import sys
from subprocess import call
import argparse
import getpass
from time import strftime
import logging


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def submit_mc_jobs_pbs(in_args=sys.argv[1:]):
    """Main function for handing user args and submitting PBS jobs."""

    # Handle user options. The user can pass all the same options as they
    # would if running the program locally. However, for certain options,
    # we interecpt the argument(s) and modify if necessary.
    parser = argparse.ArgumentParser(description=__doc__)

    # Options for the job submitter
    parser.add_argument("jobIdRange",
                        help="Specify job ID range to run over. The ID is used"
                        " as the random number generator seed, so manual "
                        "control is needed to avoid making the same files. "
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
    parser.add_argument("--massRange",
                        help="Specify mass range to run over. "
                        "Must be of the form: startMass, endMass, massStep. "
                        "For each mass point, njobs jobs will be submitted. "
                        "This will superseed any --mass option passed via --args",
                        nargs=3, type=float,
                        metavar=('startMass', 'endMass', 'massStep'))
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
    # Anything else
    parser.add_argument("--test",
                        help="Testing mode. Puts jobs into 'test' queue "
                        "with small walltime.",
                        action='store_true')
    args = parser.parse_args(args=in_args)

    log.info('>>> Creating jobs')

    if args.v:
        log.setLevel(logging.DEBUG)
        log.debug(args)

    log.debug('program args: %s' % args)

    # Do some checks
    # -------------------------------------------------------------------------
    if not os.path.isfile(args.exe):
        raise RuntimeError('Executable %s does not exist' % args.exe)

    checkJobIdRange(args.jobIdRange)

    # Get the input card from user's options
    try:
        card = get_option_in_args(args.args, "--card")
    except KeyError as e:
        log.error('You did not specify an input card!')
        raise
    if not card:
        raise RuntimeError('You did not specify an input card!')
    if not os.path.isfile(card):
        raise RuntimeError('Input card %s does not exist!' % card)
    args.card = card
    args.channel = os.path.splitext(os.path.basename(card))[0]

    # Auto generate output directory if necessary
    # -------------------------------------------------------------------------
    if args.oDir == "":
        args.oDir = generate_dir_iridis(args.channel)

    checkCreateDir(args.oDir, args.v)

    # Setup log directory
    # -------------------------------------------------------------------------
    log_dir = "PBS/logs/%s/" % generate_subdir(args.channel)
    checkCreateDir(log_dir, args.v)

    # Add in RNG seed based on arrayID
    # -------------------------------------------------------------------------
    args.args.extend(['--seed', '\\$PBS_ARRAYID'])

    # Get number of events to generate per job
    # -------------------------------------------------------------------------
    if '--number' in args.args:
        n_events = get_option_in_args(args.args, "--number")
    elif '-n' in args.args:
        n_events = get_option_in_args(args.args, "-n")
    else:
        log.warning('Number of events per job not specified - assuming 1')
        n_events = 1

    # Loop over required mass(es)
    # -------------------------------------------------------------------------
    if args.massRange:
        if any(x <= 0 for x in args.massRange):
            raise RuntimeError('You cannot have a mass <= 0')
        if args.massRange[1] < args.massRange[0]:
            raise RuntimeError('You cannot have endMass < startMass')
        masses = frange(args.massRange[0], args.massRange[1], args.massRange[2])
    else:
        masses = [get_option_in_args(args.args, '--mass')]

    for mass in masses:

        # Submit the jobs.
        # --------------------------------------------------------------------
        # The jobs will be submitted as a job array, to allow easy manipulation
        # of the set of jobs as a whole.
        pbs_script = 'PBS/mcJob.sh'
        mass_str = '%g' % mass if isinstance(mass, float) else str(mass)
        job_name = args.channel + mass_str
        job_range = '%d-%d' % (args.jobIdRange[0], args.jobIdRange[1])
        log_name = "%s_\\${PBS_JOBID%%%%[*]}" % args.channel

        exe_args = args.args[:]

        # Set mass in args
        if '--mass' in exe_args:
            set_option_in_args(exe_args, '--mass', str(mass))
        else:
            exe_args.extend(['--mass', mass])

        # Set filenames in args. Ensures seed and output directory
        # added to filenames.
        for fmt in ['hepmc', 'root', 'lhe']:
            # special warning for hepmc files
            flag = '--%s' % fmt
            if fmt == "hepmc" and flag not in exe_args:
                log.warning("You didn't specify --hepmc in your --args. "
                            "No HepMC file will be produced.")
            if flag not in exe_args:
                continue
            else:
                # Auto generate output filename if necessary
                # Bit hacky as have to manually sync with PythiaProgramOpts
                if not get_option_in_args(args.args, flag):
                    out_name = "%s_ma1_%s_n%s.%s" % (args.channel, mass,
                                                     n_events, fmt)
                    set_option_in_args(exe_args, flag, out_name)

                # Use the filename itself, ignore any directories from user.
                out_name = os.path.basename(get_option_in_args(exe_args, flag))

                # Add in seed/job ID to filename. Note that generateMC.cc a
                # dds the seed to the auto-generated filename, so we only
                # need to modify it if the user has specified the name
                out_name = "%s_seed\\${PBS_ARRAYID}.%s" % (os.path.splitext(out_name)[0], fmt)
                out_name = os.path.join(args.oDir, out_name)
                set_option_in_args(exe_args, flag, out_name)

        script_vars = {'exe': args.exe,
                       'args': " ".join(exe_args)}

        if args.test:
            pbs_opts = {'-q': 'test', '-l': 'walltime=0:30:00'}
        else:
            pbs_opts = None

        if args.v:
            log.debug(script_vars)
            log.debug(pbs_opts)

        if not args.dry:
            submit_pbs_job(pbs_script, job_name=job_name, array_ids=job_range,
                           log_dir=log_dir, log_name=log_name,
                           script_vars=script_vars, pbs_opts=pbs_opts)


def checkJobIdRange(jobIdRange):
    """Checks range of job IDs. Will raise a RuntimeError if unsatisfactory.

    jobIdRange: list of ints, length 2.
    """
    if jobIdRange[0] < 1:
        raise RuntimeError('The first jobIdRange argument must be >= 1.')

    if jobIdRange[1] < jobIdRange[0]:
        raise RuntimeError('The second jobIdRange argument must be >= the first.')


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


def generate_dir_iridis(channel):
    """Generate a directory name on Iridis using userId, channel, and date.

    >>> generate_dir_iridis('ggh_4tau')
    /scratch/<username>/NMSSMPheno/Pythia8/ggh_4tau/<date>
    """
    uid = getpass.getuser()
    return "/scratch/%s/NMSSMPheno/Pythia8/%s" % (uid, generate_subdir(channel))


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


def set_option_in_args(args, flag, value):
    """Set value for flag in list of args.

    If no value already exists, it will insert the value after the flag.
    If the flag does not appear in args, a KeyError will be raised.

    >>> args = ['--foo', 'bar', '--man', '--pasta']
    >>> set_option_in_args(args, '--foo', 'ball')
    >>> args
    ['--foo', 'ball', '--man', '--pasta']
    >>> set_option_in_args(args, '--man', 'trap')
    >>> args
    ['--foo', 'ball', '--man', 'trap', --pasta']
    >>> set_option_in_args(args, '--pasta', 'bake')
    >>> args
    ['--foo', 'ball', '--man', 'trap', --pasta', 'bake']

    """
    # first check if a value already exists.
    if get_option_in_args(args, flag):
        args[args.index(flag) + 1] = value
    else:
        if flag == args[-1]:
            # if the flag is the last entry in args
            args.append(value)
        elif args[args.index(flag) + 1].startswith('-'):
            # if the next entry is a flag, we need to insert our value
            args.insert(args.index(flag) + 1, value)


def submit_pbs_job(script,
                   job_name=None, array_ids="",
                   log_dir=".", log_name=None,
                   script_vars=None, pbs_opts=None):
    """Submit a PBS job.

    script: str
        Script to submit with qsub.

    job_name: Optional[str]
        Name for job(s), as shown in `qstat`

    array_ids: Optional[str]
        Specify the array job IDs. See qsub man page (-t flag) for details.
        e.g:
        "1-10" will submit 10 jobs with array IDs 1, ..., 10.
        "1,3,5" will submit 3 jobs with array IDs 1, 3, and 5.
        "2-6:2" will submit 3 jobs, with IDs 2, 4 and 6. The ":2" specifies
        the increment between job IDs.

    log_dir: Optional[str]
        Directory to store STDOUT/STDERR output log files. Default is "."

    log_name: Optional[str]
        Filename stem for STDOUT/STDERR output log files. Log files will
        then be written to <log_dir>/<log_name>.[out|err].
        Default is "$PBS_JOBID.$PBS_ARRAYID".

    script_vars: Optional[dict]
        A dict of variables and their values to pass to the qsub script.
        e.g. {'args': '--n 10 --card ggh.cmnd'}

    pbs_opts: Optional[dict]
        A dict of other options to pass to qsub.
        Must be of the form {arg: value}, e.g. {'-q': 'batch'}
    """

    stdout_name = os.path.join(log_dir, log_name + ".out") if log_name and log_dir else None
    stderr_name = os.path.join(log_dir, log_name + ".err") if log_name and log_dir else None

    cmds = ['qsub']
    # Add options to qsub, if the user requested them
    opt_dict = {'-N': job_name,
                '-o': stdout_name,
                '-e': stderr_name,
                '-t': array_ids}
    for k, v in opt_dict.iteritems():
        if v:
            cmds.extend([k, v])

    if script_vars:
        script_var_str = ",".join(['%s="%s"' % (k, v) for k, v in script_vars.iteritems()])
        cmds.extend(['-v', script_var_str])

    if pbs_opts:
        for k, v in pbs_opts.iteritems():
            cmds.extend([k, v])

    cmds.append(script)
    print 'Submitting jobs to queue'
    print ' '.join(cmds)
    call(cmds)


def frange(start, stop, step=1.0):
    """Generate an iterator to loop over a range of floats."""
    i = start
    while i <= stop:
        yield i
        i += step


if __name__ == "__main__":
    submit_mc_jobs_pbs()
