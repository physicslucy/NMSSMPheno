#!/usr/bin/env python

"""
Script to run MG5_aMC locally. Creates new input card from user's options,
to ensure that Pythia8 & HepMC linked correctly, and other options.
"""

import argparse
import sys
import os
import re
import logging
from subprocess import call


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def run_mg5(in_args=sys.argv[1:]):
    """Main fn"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('card',
                        help='card file to pass to MG5_aMC')
    parser.add_argument('--exe',
                        help='Location of mg5_aMC executable',
                        default="mg5_aMC")
    parser.add_argument('-n', '--number',
                        dest='nevents',
                        help='Number of events to generate',
                        type=int)
    parser.add_argument('--seed',
                        dest='iseed',
                        help='Random number generator seed',
                        type=int)
    parser.add_argument('--pythia8',
                        dest='pythia8_path',
                        help='Path to Pythia directory',
                        required=True)
    parser.add_argument('--hepmc',
                        help='Path to HepMC install directory',
                        required=True)
    # parser.add_argument('--option',
    #                     nargs=2,
    #                     action='append',
    #                     help='Allow replacement of any other options. '
    #                     'Specify as: --option OPTION VALUE, for as many '
    #                     'options as you wish to change '
    #                     'e.g. --option ickkw 3 --option Qcut 15')
    parser.add_argument('--dry',
                        action='store_true',
                        help="Only make card, don't run MG5_aMC")
    parser.add_argument('--new',
                        help='Filename for new card. '
                        'If not specified, defaults to <card>_new.txt')
    parser.add_argument("-v",
                        action='store_true',
                        help="Display debug messages.")
    args = parser.parse_args(in_args)
    if args.v:
        log.setLevel(logging.DEBUG)
        log.debug(args)

    # Use script args to create dict of fields to replace in card
    if 'hepmc' in args:
        args.__dict__['extrapaths'] = "../lib %s" % os.path.join(os.path.abspath(args.hepmc), 'lib')
        args.__dict__['includepaths'] = os.path.join(os.path.abspath(args.hepmc), 'include')

    mg_vars = ['nevents', 'iseed', 'pythia8_path', 'extrapaths', 'includepaths']
    fields = {k: args.__dict__[k] for k in mg_vars if args.__dict__[k]}

    log.debug(fields)

    # make a new card for MG5_aMC
    new_card = args.card.replace(".txt", "_new.txt")
    args.__dict__['new_card'] = new_card
    make_card(args.card, new_card, fields)

    # run MG5_aMC
    if not args.dry:
        log.info('Running MG5_aMC with card %s' % new_card)
        mg5_cmds = [os.path.abspath(args.exe), new_card]
        log.debug(mg5_cmds)
        call(mg5_cmds)

    return args


def make_card(in_card, out_card, fields):
    """Make a copy of a card file, replacing various attributes.

    The attribute replacement is made if a line contains a variable name as
    a word surrounded by spaces.

    in_card: str.
        Name of card to use as template.
    out_card: str
        Name of card to produce.
    fields: dict
        Dict of thing to replace in the template card. Dict should be of the
        form, {<var_name>: <value>}. var_name must be a str.
        <var_name> is the name of a MG5 variable.
        <value> is the value of that variable.
        A replacement will occur if the line contains the <var_name> as a word.
        So if <var_name> = "nevents", "set run_card nevents 200" would match,
        but "output genevents" would not match.

    For example:
    >>> fields = {'nevents': '200', 'output': 'new_process'}
    >>> make_card('old_card.txt', 'new_card.txt', fields)
    """
    with open(in_card) as in_file:
        card_template = in_file.readlines()  # hmm read or readlines

    for name, value in fields.iteritems():
        log.debug('Setting %s for %s' % (value, name))
        p = re.compile(name + r' (.*)$')

        for i, line in enumerate(card_template):
            # skip empty or comment lines
            if not line or line.startswith('#') or name not in line:
                continue
            try:
                # get old values to replace
                old_values = p.search(line).group(1)
            except IndexError as e:
                log.error('Error finding line with %s in card' % name)
                raise
            card_template[i] = line.replace(old_values, str(value))

    log.info('Writing new card to %s' % out_card)
    with open(out_card, 'w') as out_file:
        out_file.write(''.join(card_template))


if __name__ == "__main__":
    run_mg5()
