#!/usr/bin/env python
"""
Script to submit a batch of Delphes jobs on HTCondor
"""


import argparse
import sys
import os
import logging
from time import strftime
from subprocess import call
from itertools import izip_longest


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


# Set the local Delphes installation directory here
DELPHES_DIR = '/users/%s/delphes' % os.environ['LOGNAME']


def submit_delphes_jobs_htcondor(in_args=sys.argv[1:], delphes_dir=DELPHES_DIR):
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card',
                        required=True,
                        help='Delphes card file. ASSUMES IT IS IN input_cards/')
    parser.add_argument('--iDir',
                        required=True,
                        help='Input directory of hepmc/lhe files to process')
    parser.add_argument('--type',
                        choices=['hepmc', 'lhe'],
                        help='Filetype to process')
    parser.add_argument('--oDir',
                        help='Output directory for ROOT files. If one is not '
                        'specified, one will be created automatically at '
                        '<iDir>/../delphes/<card>')
    # Some generic script options
    parser.add_argument("--dry",
                        help="Dry run, don't submit to queue.",
                        action='store_true')
    parser.add_argument("-v",
                        help="Display debug messages.",
                        action='store_true')
    args = parser.parse_args(args=in_args)

    log.info('>>> Creating jobs')

    if args.v:
        log.setLevel(logging.DEBUG)

    log.debug('program args: %s' % args)

    # Do some checks
    # -------------------------------------------------------------------------
    if not os.path.isdir(delphes_dir):
        raise RuntimeError('DELPHES_DIR does not correspond to an actual directory')
    if not os.path.isdir(args.iDir):
        raise RuntimeError('--iDir arg does not correspond to an actual directory')
    if not os.path.isfile(args.card):
        raise RuntimeError('Cannot find input card')
    if os.path.dirname(args.card) != 'input_cards':
        raise RuntimeError('Put your card in input_cards directory')

    # Avoid issues with os.path.dirname as we want parent directory, not itself
    if args.iDir.endswith('/'):
        args.iDir = args.iDir.rstrip('/')
    if delphes_dir.endswith('/'):
        delphes_dir = delphes_dir.rstrip('/')

    # Auto-generate output dir if not specified
    # -------------------------------------------------------------------------
    if not args.oDir:
        args.oDir = generate_output_dir(args.iDir, os.path.basename(args.card))
    check_create_dir(args.oDir, args.v)

    # Setup log directory
    # -------------------------------------------------------------------------
    log_dir = '%s/logs' % (generate_subdir(args.card))
    check_create_dir(log_dir, args.v)

    # File stem common for all dag and status files
    # -------------------------------------------------------------------------
    file_stem = os.path.join(generate_subdir(args.card), strftime("%H%M%S"))
    check_create_dir(os.path.dirname(file_stem), args.v)

    # Dicts to hold thing to be copied before/after the job runs
    copy_to_local = {}
    copy_from_local = {}

    # Zip up Delphes installation and move it to hdfs
    # -------------------------------------------------------------------------
    log.info('Creating tar file of Delphes installation, please wait...')
    call(['tar', 'czf', 'delphes.tgz', '-C', os.path.dirname(delphes_dir), os.path.basename(delphes_dir)])
    zip_dir = '/hdfs/user/%s/NMSSMPheno/zips' % (os.environ['LOGNAME'])
    check_create_dir(zip_dir, args.v)
    zip_filename = 'delphes.tgz'
    zip_path = os.path.join(zip_dir, zip_filename)
    call(['hadoop', 'fs', '-copyFromLocal', '-f', zip_filename, zip_dir.replace('/hdfs', '')])
    os.remove(zip_filename)
    copy_to_local[zip_path] = zip_filename

    # Copy across card to hdfs
    # -------------------------------------------------------------------------
    if not args.dry:
        log.debug('Copying across input_cards...')
        call(['hadoop', 'fs', '-copyFromLocal', '-f',
              'input_cards', args.oDir.replace('/hdfs', '')])
    copy_to_local[os.path.join(args.oDir, 'input_cards')] = 'input_cards'

    # Write DAG file
    # -------------------------------------------------------------------------
    dag_name = file_stem + '.dag'
    status_name = file_stem + '.status'

    write_dag_file(dag_filename=dag_name,
                   condor_filename='HTCondor/runDelphes.condor',
                   status_filename=status_name,
                   copyToLocal=copy_to_local, copyFromLocal=copy_from_local,
                   log_dir=log_dir, args=args)

    # Submit it
    # -------------------------------------------------------------------------
    if args.dry:
        log.warning('Dry run - not submitting jobs or copying files.')
    else:
        call(['condor_submit_dag', dag_name])
        log.info('Check status with:')
        log.info('DAGstatus.py %s' % status_name)
        log.info('Condor log files written to: %s' % log_dir)
        print''


def write_dag_file(dag_filename, condor_filename, status_filename, log_dir,
                   copyToLocal, copyFromLocal, args):
    """Write a DAG file for a set of jobs

    Creates a DAG file, setting correct args for worker node script.
    dag_filename: str
        Name to be used for DAG job file.
    condor_filename: str
        Name of condor job file to be used for each job.
    status_filename: str
        Name to be used for DAG status file.
    copyToLocal: dict{str : str}
        Dict of things to copyToLocal when the worker node script starts.
        Of the form source : destination
    copyFromLocal: dict{str : str}
        Dict of things to copyFromLocal when the worker node script ends.
        Of the form source : destination
    args: argparse.Namespace
        Contains info about output directory, job IDs, number of events per job,
        and args to pass to the executable.

    """
    # collate list of input files
    def accept_file(filename):
        fl = os.path.basename(filename).lower()
        extensions = ['.lhe', '.hepmc', '.gz', '.tar.gz', '.tgz']
        return any([os.path.isfile(filename) and fl.endswith(ext) for ext in extensions])

    print os.listdir(args.iDir)
    input_files = [os.path.join(args.iDir, f) for f in os.listdir(args.iDir) if accept_file(os.path.join(args.iDir, f))]
    if not input_files:
        raise RuntimeError('No acceptable input file in %s' % args.iDir)

    log.info("DAG file: %s" % dag_filename)
    with open(dag_filename, 'w') as dag_file:
        dag_file.write('# DAG for card %s\n' % args.card)
        dag_file.write('# Outputting to %s\n' % args.oDir)

        # we assign each job to run over a certain number of input files.
        files_per_job = 2
        for ind, input_files in enumerate(grouper(input_files, files_per_job)):
            job_name = '%d_%s' % (ind, os.path.basename(args.card))
            dag_file.write('JOB %s %s\n' % (job_name, condor_filename))

            # args to pass to the script on the worker node
            job_opts = ['--card', args.card]
            if args.type:
                exe_dict = {'hepmc': './DelphesHepMC', 'lhe': './DelphesLHEF'}
                job_opts.extend(['--exe', exe_dict[args.type]])

            # Add process commands to job opts
            # ----------------------------------------------------------------
            # generate output filenames
            def stem(filename):
                # do the splitext twice to get rid of e.g. X.tar.gz
                return os.path.splitext(os.path.splitext(os.path.basename(filename))[0])[0]
            output_files = [os.path.join(args.oDir, stem(f)) + '.root' for f in input_files]
            for in_file, out_file in zip(input_files, output_files):
                job_opts.extend(['--process', in_file, out_file])

            # start with files to copyToLocal at the start of job running
            # ----------------------------------------------------------------
            if copyToLocal:
                for src, dest in copyToLocal.iteritems():
                    job_opts.extend(['--copyToLocal', src, dest])

            # add in any other files that should be copied from the worker at
            # the end of the job
            # ----------------------------------------------------------------
            if copyFromLocal:
                for src, dest in copyFromLocal.iteritems():
                    job_opts.extend(['--copyFromLocal', src, dest])
            log.debug('job_opts: %s' % job_opts)

            # write job vars to file
            log_name = os.path.splitext(os.path.basename(dag_filename))[0]
            dag_file.write('VARS %s opts="%s" logDir="%s" logFile="%s"\n' % (
                           job_name, ' '.join(job_opts), log_dir, log_name))

        dag_file.write('NODE_STATUS_FILE %s 30\n' % status_filename)


def check_create_dir(directory, info=False):
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


def generate_output_dir(input_dir, card):
    """Generate an output directory based on the input directory and card name.

    >>> generate_output_dir('/hdfs/users/rob/hepmc', 'delphes_card_cms.tcl')
    /hdfs/users/rob/delphes/delphes_card_cms/
    """
    if input_dir.endswith('/'):
        input_dir = input_dir.rstrip('/')
    return os.path.join(os.path.dirname(input_dir), 'delphes', os.path.splitext(card)[0])


def generate_subdir(card):
    """Generate subdirectory name using the card name and date.
    Can be used for output and log files, so consistent between both.
    """
    return os.path.join(os.path.splitext(os.path.basename(card))[0], strftime("%d_%b_%y"))


def grouper(iterable, n, fillvalue=None):
    """
    Iterate through iterable in groups of size n.
    If < n values available, pad with fillvalue.

    Taken from the itertools cookbook.
    """
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

if __name__ == "__main__":
    submit_delphes_jobs_htcondor()
