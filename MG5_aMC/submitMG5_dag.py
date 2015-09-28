#!/usr/bin/env python
"""
Submit lots of MG5_aMC jobs to condor. All jobs run using the same input card.

The user should specify an input card with MG5_aMC instructions, an output
directory on /hdfs, the number of events to generate per job, and the
total number of job to submit. There is also the option for a 'dry run' where
all the files & directories are set up, but the job is not submitted.

Note that this submits the jobs not one-by-one but as a DAG, to allow easier
monitoring of job status.
"""


from time import strftime
from subprocess import call
import argparse
import sys
import os


def submit(in_args=sys.argv[1:]):
    """
    Main function. Sets up all the relevant directories, makes condor
    job and DAG files, then submits them if necessary.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('card',
                        help='Specify input card.')
    parser.add_argument('oDir',
                        help='Output directory. A subdirectory " \
                        "<oDir>/<card>/hepmc will be created for output files.')
    parser.add_argument('--nEvents',
                        help='Number of events to generate per job',
                        type=int)
    parser.add_argument('--nJobs',
                        help='Number of jobs',
                        type=int)
    parser.add_argument('--dry',
                        help="Dry run. Don't submit jobs.",
                        action='store_true')
    args = parser.parse_args(in_args)

    # -------------------------------------------------------------------------
    # Do some checks, make directories
    # -------------------------------------------------------------------------
    if not os.path.isfile(args.card):
        raise RuntimeError("Cannot find specified card %s", args.card)

    # Directory for hepmc files
    channel = os.path.splitext(os.path.basename(args.card))[0]
    output_dir = os.path.join(args.oDir, channel, 'hepmc')
    if not os.path.isdir(output_dir):
        print 'Making directory for hepmc files:', output_dir
        os.makedirs(output_dir)

    # Directory for output logs, etc
    date = strftime("%d_%b_%y")
    time = strftime("%H%M%S")
    log_dir = 'logs/%s/%s_%s' % (date, channel, time)
    if not os.path.isdir(log_dir):
        print 'Making directory for log files:', log_dir
        os.makedirs(log_dir)

    # File stem common for all condor, dag, status files
    file_stem = 'mg5_%s_%s_%s' % (channel, date, time)

    # -------------------------------------------------------------------------
    # Make a condor job for this batch using the template
    # -------------------------------------------------------------------------
    script_name = file_stem + '.condor'
    print 'Condor job file:', script_name
    with open('runMG5_aMC.condor', 'r') as template:
        job_template = template.read()

    job_description = job_template.replace('SEDLOG', log_dir)
    job_description = job_description.replace('SEDOUTPUT', output_dir)
    job_description = job_description.replace('SEDCARD', args.card)

    with open(script_name, 'w') as job_file:
        job_file.write(job_description)

    # -------------------------------------------------------------------------
    # Make DAG file with the date and time
    # -------------------------------------------------------------------------
    dag_name = file_stem + '.dag'
    status_name = file_stem + '.status'
    print "DAG file:", dag_name
    with open(dag_name, 'w') as dag_file:
        dag_file.write('# DAG for card %s\n' % args.card)
        dag_file.write('# Running %d jobs\n' % args.nJobs)
        dag_file.write('# Each generating %d events\n' % args.nEvents)
        dag_file.write('\n')
        for job_ind in xrange(args.nJobs):
            job_name = '%s_%d' % (channel, job_ind)
            dag_file.write('JOB %s %s\n' % (job_name, script_name))
            job_vars = '-c %s -n %d -o %s' % (os.path.basename(args.card),
                                              args.nEvents,
                                              output_dir)
            dag_file.write('VARS %s opts="%s"\n' % (job_name, job_vars))
        dag_file.write('NODE_STATUS_FILE %s\n' % status_name)

    # -------------------------------------------------------------------------
    # Submit it
    # -------------------------------------------------------------------------
    if not args.dry:
        call(['condor_submit_dag', dag_name])
        print 'Check status with:'
        print 'DAGstatus.py', status_name
        print ''
        print 'Condor log files written to:', log_dir


if __name__ == "__main__":
    submit()
