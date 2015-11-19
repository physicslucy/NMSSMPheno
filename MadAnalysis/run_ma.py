#!/usr/bin/env python
"""
Run MadAnalysis locally.

Takes care of untarring input files, etc.
"""


import os
import sys
import argparse
import json
import logging
from subprocess import call


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


class MadAnalysisArgParser(argparse.ArgumentParser):
    """
    Class to handle parsing of options. This allows it to be used in other
    scripts (e.g. for HTCondor/PBS batch scripts)
    """
    def __init__(self, *args, **kwargs):
        super(MadAnalysisArgParser, self).__init__(*args, **kwargs)
        self.add_arguments()

    def add_arguments(self):
        self.add_argument('samples',
                          help='JSON with sample names and locations')
        self.add_argument('--exe',
                          help='Location of MadAnalysis executable',
                          default="MadAnalysis5Job")
        self.add_argument('--dry',
                          action='store_true',
                          help="Only make card, don't run MadAnalysis")
        self.add_argument("-v",
                          action='store_true',
                          help="Display debug messages.")


def run_ma(in_args=sys.argv[1:]):
    """Main routine"""
    parser = MadAnalysisArgParser(description=__doc__)
    args = parser.parse_args(in_args)
    if args.v:
        log.setLevel(logging.DEBUG)
        log.debug(args)

    # Do some checks
    # ------------------------------------------------------------------------
    if not os.path.isfile(args.samples):
        raise RuntimeError('JSON samples file does not exist')
    if not os.path.isfile(args.exe):
        raise RuntimeError('MadAnalysis exe does not exist')

    # Interpret samples JSON
    # ------------------------------------------------------------------------
    # create a filelist for each set of samples.
    with open(args.samples) as jfile:
        sample_dict = json.load(jfile)
    log.debug('Sample dictionary: %s' % sample_dict)

    filelists = generate_filelists(sample_dict, os.getcwd())

    # Run MadAnalysis
    # ------------------------------------------------------------------------
    # we make a temporary inner directory to run from since the output from
    # MadAnalysis will be put in $PWD/../Output/
    if not args.dry:
        exe_abs = os.path.abspath(args.exe)
        tmp_dir = 'run_dir'
        if not os.path.isdir(tmp_dir):
            os.makedirs(tmp_dir)
        os.chdir(tmp_dir)
        for flist in filelists:
            call([exe_abs, flist])


def generate_filelists(sample_dict, out_dir):
    """Generate list of files suitable for use as input to MadAnalysis.
    Each file list will be named after the sample it represents.

    Returns a list of the absolute filepaths for the file lists.

    sample_dict: dict
        Dict of info for channels. Key is the channel name, value is a
        dict of information about the channel.
        Channels starting with #, !, _ will be ignored.
    out_dir: str
        Output directory for filelists.
    """
    return [create_filelist(channel, chan_dict, out_dir)
            for channel, chan_dict in sample_dict.iteritems()
            if channel[0] not in ['#', '!', '_']]


def create_filelist(channel, chan_dict, out_dir):
    """Create a filelist suitable for passing to MadAnalysis.
    Returns filename of filelist.

    channel: str
        Name of the channel. Used for the filelist filename.
    chan_dict: dict
        Dictionary of info corresponding to each channel
    out_dir: str
        Output directory for filelist.
    """
    filename = os.path.join(out_dir, channel)

    def dir_file_iter(dirs, ext):
        for d in dirs:
            for f in os.listdir(d):
                if (ext and f.endswith(ext)) or not ext:
                    yield os.path.join(d, f)

    with open(filename, 'w') as flist:
        log.debug('Writing filelist %s' % channel)
        n_files = chan_dict['num']
        for i, f in enumerate(dir_file_iter(chan_dict['dirs'], '.root')):
            if i >= n_files and n_files > 0:
                break
            flist.write('%s\n' % f)

    return filename


if __name__ == "__main__":
    run_ma()