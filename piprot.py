#!/usr/bin/env python
import argparse
from datetime import datetime
import os
import requests
import time
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

PYPI_BASE_URL = 'https://pypi.python.org/pypi/'


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


def parse_requirements_file(req_file, lint, colour=TextColours(False)):
    """Take a file and return a dict of (requirement, versions) based
    on the files requirements specs.
    """
    req_dict = {}
    requirements = req_file.readlines()

    # TODO parse with regex
    for requirement in requirements:
        if '-r' in requirement[:3]:
            r, filename = requirement.replace('\n', '').strip().split(' ')
            #print 'Getting a little recursive, are we?'
            req_dict.update(parse_requirements_file(open(os.path.join(os.path.dirname(req_file.name), filename)), lint, colour=colour))

        requirement = requirement.replace('\n', '').strip().split(' ')[0]
        if requirement and requirement[0] not in ['#', '-'] and 'git' not in requirement:
            try:
                requirement, version = requirement.split('==')
                req_dict[requirement] = version
                #print requirement, version
            except ValueError:
                # what are you doing!
                if lint:
                    print '%s%s doesn\'t have a version number%s' % \
                                (colour.FAIL, requirement, colour.ENDC)
    return req_dict


def get_release_date(requirement, version=None, colour=TextColours(False)):
    j = None
    try:
        j = requests.request('GET', get_pypi_url(requirement, version)).json()
    except requests.HTTPError:
        if version:
            print '%s%s (%s) isn\'t available on PyPi anymore!%s' % \
                    (colour.FAIL, requirement, version, colour.ENDC)
        else:
            print '%s%s isn\'t even on PyPi. Check that the project still exists!%s' % \
                    (colour.FAIL, requirement, colour.ENDC)
        return None

    try:
        d = j['urls'][0]['upload_time']
        return datetime.fromtimestamp(time.mktime(time.strptime(d, '%Y-%m-%dT%H:%M:%S')))
    except IndexError:
        print '%s%s (%s) didn\'t return a date property%s' % (colour.FAIL, requirement, version, colour.ENDC)


def main(req_files=[], do_lint=False, do_colour=False, verbosity=0):
    """Process a list of requirements to determine how out of date they are.
    """
    colour = TextColours(do_colour)
    requirements = {}
    for req_file in req_files:
        requirements.update(parse_requirements_file(req_file, do_lint, colour))
        req_file.close()

    # close all files.
    # remove duplicate requirements lines.
    # divide requirements between a number of multiprocessing workers.

    total_time_delta = 0
    for req, version in requirements.items():
        latest_version = get_release_date(req, colour=colour)
        specified_version = get_release_date(req, version, colour=colour)

        if latest_version and specified_version:
            time_delta = (latest_version - specified_version).days
            total_time_delta = total_time_delta + time_delta

            if verbosity:
                if time_delta > 0:
                    print '%s%s (%s) is %s days out of date%s' % \
                      (colour.FAIL, req, version, time_delta,
                       colour.ENDC)
                else:
                    print '%s%s (%s) is up to date%s' % \
                        (colour.OKGREEN, req, version, colour.ENDC)

    if total_time_delta > 0:
        print "%sYour requirements are %s days out of date%s" % \
          (colour.FAIL, total_time_delta, colour.ENDC)
    else:
        print "%sLooks like you've been keeping up to date, better go back to taming that beard!%s" % \
          (colour.OKGREEN, colour.ENDC)


if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser(
        epilog="Here's hoping your requirements are nice and fresh!"
        )
    cli_parser.add_argument('-l', '--lint', action='store_true',
                            help='lint the requirements')
    cli_parser.add_argument('-c', '--colour', '--color', action='store_true',
                            help='coloured output')
    cli_parser.add_argument('-v', '--verbose', action='count',
                            help='verbosity, can be supplied more than once')
    cli_parser.add_argument('file', nargs='+', type=argparse.FileType(),
                            help='requirements file(s), use `-` for stdin')
    cli_args = cli_parser.parse_args()

    # call the main function to kick off the real work
    main(req_files=cli_args.file, do_lint=cli_args.lint,
         do_colour=cli_args.colour, verbosity=cli_args.verbose)
