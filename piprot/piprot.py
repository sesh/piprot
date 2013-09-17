#!/usr/bin/env python
from __future__ import print_function
import argparse
from datetime import datetime
import os
import re
import requests
import sys
import time
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO
import json

VERSION = "0.1.4"
PYPI_BASE_URL = 'https://pypi.python.org/pypi'
NOTIFY_URL = 'http://localhost:9000/'


class TextColours:
    def __init__(self, enabled=False):
        if enabled:
            self.enable()
        else:
            self.disable()

    def enable(self):
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


def get_pypi_url(requirement, version=None):
    if version:
        return '{base}/{req}/{version}/json'.format(base=PYPI_BASE_URL,
            req=requirement, version=version)
    else:
        return '{base}/{req}/json'.format(base=PYPI_BASE_URL, req=requirement)


def parse_req_file(req_file, colour=TextColours(False)):
    """Take a file and return a dict of (requirement, versions) based
    on the files requirements specs.

    TODO support pip's --index-url and --find-links requirements lines.
    TODO support Git, Subversion, Bazaar, Mercurial requirements lines.
    """
    req_dict = {}
    requirements = req_file.readlines()
    for requirement in requirements:
        if requirement.strip().startswith('#'):
            continue

        # if matching recursive requirement spec., call myself again
        recursive = re.match('\s*-r\s+(?P<filename>\S+)', requirement)
        if recursive:
            try:
                r_req_file = open(os.path.join(os.path.dirname(req_file.name),
                                               recursive.group('filename')))
                req_dict.update(parse_req_file(r_req_file, colour=colour))
            except IOError:
                print >> sys.stderr, '{} could not be opened'.format(
                    recursive.group('filename')
                )
                continue

        # if matching requirement line (Thing==1.2.3), update dict, continue
        req_match = re.match('\s*(?P<package>\S+)==(?P<version>\S+)',
                             requirement)
        if req_match:
            req_dict[req_match.group('package')] = req_match.group('version')
            continue

        # it matching VCS requirement spec., log to stderr, continue
        vcs_match = re.match(
            '\s*(-e){0,1}\s+(?P<vcsscheme>(svn|git|hg|bzr))\+',
            requirement)

        if vcs_match:
            print >> sys.stderr, 'VCS requirements not yet supported'
            continue
        # if matches weird '>=1.2' format, log a warning, continue
        # if no version spec, log a warning, continue
        # if anything else, log a warning, continue?
    return req_dict


def get_version_and_release_date(requirement, version=None, colour=TextColours(False)):
    response = None
    try:
        response = requests.get(get_pypi_url(requirement, version)).json()
    except requests.HTTPError:
        if version:
            print ('%s%s (%s) isn\'t available on PyPi anymore!%s' %
                (colour.FAIL, requirement, version, colour.ENDC))
        else:
            print ('%s%s isn\'t even on PyPi. Check that the project'
                ' still exists!%s' %
                (colour.FAIL, requirement, colour.ENDC))
        return None, None
    #TODO: Catch something more specific
    except:
        print ('%sDecoding the JSON response for %s (%s) failed%s' %
                (colour.FAIL, requirement, version, colour.ENDC))
        return None, None

    try:
        version = response['info']['stable_version']
        release_date = response['urls'][0]['upload_time']
        if not version:
            version = response['info']['version']

        return version, datetime.fromtimestamp(time.mktime(
            time.strptime(release_date, '%Y-%m-%dT%H:%M:%S')
        ))
    except IndexError:
        print ('%s%s (%s) didn\'t return a date property%s' %
            (colour.FAIL, requirement, version, colour.ENDC))
        return None, None


def main(req_files=[], do_colour=False, verbosity=0, latest=False):
    """
        Process a list of requirements to determine how out of date they are.
    """
    colour = TextColours(do_colour)
    requirements = {}
    for req_file in req_files:
        requirements.update(parse_req_file(req_file, colour))
        req_file.close()

    # close all files.
    # remove duplicate requirements lines.
    
    total_time_delta = 0
    for req, version in requirements.items():
        latest_version, latest_release_date = get_version_and_release_date(req, colour=colour)
        specified_version, specified_release_date = get_version_and_release_date(req, version, colour=colour)

        if latest_release_date and specified_release_date:
            time_delta = (latest_release_date - specified_release_date).days
            total_time_delta = total_time_delta + time_delta

            if verbosity:
                if time_delta > 0:
                    print('%s%s (%s) is %s days out of date%s' %
                          (colour.FAIL, req, version, time_delta, colour.ENDC), file=sys.stderr)
                else:
                    print('%s%s (%s) is up to date%s' %
                        (colour.OKGREEN, req, version, colour.ENDC))

            if latest and latest_version != specified_version:
                print('{}=={} # Updated from {}'.format(req, latest_version, specified_version))

    if total_time_delta > 0:
        print("%sYour requirements are %s days out of date%s" %
              (colour.FAIL, total_time_delta, colour.ENDC), file=sys.stderr)
    else:
        print("%sLooks like you've been keeping up to date, time for a "
              "delicious beverage!%s" % (colour.OKGREEN, colour.ENDC))


def piprot():
    cli_parser = argparse.ArgumentParser(
        epilog="Here's hoping your requirements are nice and fresh!"
    )
    cli_parser.add_argument('-c', '--colour', '--color', action='store_true',
                            help='coloured output')
    cli_parser.add_argument('-v', '--verbose', action='count',
                            help='verbosity, can be supplied more than once')
    cli_parser.add_argument('-l', '--latest', action='store_true',
                            help='print the lastest available version for out of date requirements')

    # if there is a requirements.txt file, use it by default. Otherwise print
    # usage if there are no arguments.
    nargs = '+'
    default = None
    if os.path.isfile('requirements.txt'):
        nargs = '*'
        default = [open('requirements.txt')]

    cli_parser.add_argument('file', nargs=nargs, type=argparse.FileType(),
                            default=default,
                            help='requirements file(s), use `-` for stdin')

    cli_args = cli_parser.parse_args()

    # call the main function to kick off the real work
    main(req_files=cli_args.file, do_colour=cli_args.colour,
         verbosity=cli_args.verbose, latest=cli_args.latest)

if __name__ == '__main__':
    piprot()
