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


def get_pypi_url(requirement, version=None):
    if version:
        return '{base}/{req}/{version}/json'.format(base=PYPI_BASE_URL,
            req=requirement, version=version)
    else:
        return '{base}/{req}/json'.format(base=PYPI_BASE_URL, req=requirement)


def parse_req_file(req_file, verbatim=False):
    """Take a file and return a dict of (requirement, versions) based
    on the files requirements specs.

    TODO support pip's --index-url and --find-links requirements lines.
    TODO support Git, Subversion, Bazaar, Mercurial requirements lines.
    """
    req_list = []
    requirements = req_file.readlines()
    for requirement in requirements:
        requirement_no_comments = requirement.split('#')[0].strip()
        # if matching requirement line (Thing==1.2.3), update dict, continue
        req_match = re.match('\s*(?P<package>\S+)==(?P<version>\S+)',
                             requirement_no_comments)
        if req_match:
            req_list.append((req_match.group('package'), 
                             req_match.group('version')))
        elif requirement_no_comments.startswith('-r'):
            base_dir = os.path.dirname(os.path.abspath(req_file.name))
            file_name = requirement_no_comments.split(' ')[1]
            new_path = os.path.join(base_dir, file_name)
            try:
                if verbatim:
                    req_list.append((None, requirement))
                req_list.extend(parse_req_file(open(new_path), verbatim=verbatim))
            except IOError:
                print('Failed to import {}'.format(file_name))
        elif verbatim:
            req_list.append((None, requirement))
    return req_list


def get_version_and_release_date(requirement, version=None, verbose=False):
    response = None
    try:
        response = requests.get(get_pypi_url(requirement, version)).json()
    except requests.HTTPError:
        if version:
            if verbose:
                print ('{} ({}) isn\'t available on PyPi anymore!'.format(
                        requirement, version))
        else:
            if verbose:
                print ('{} isn\'t even on PyPi. Check that the project still exists!'.format(
                        requirement))
        return None, None
    #TODO: Catch something more specific
    except:
        if verbose:
            print ('Decoding the JSON response for {} ({}) failed'.format(requirement, version))
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
        if verbose:
            print ('{} ({}) didn\'t return a date property'.format(requirement, version))
        return None, None


def main(req_files=[], verbosity=0, latest=False, verbatim=False, print_only=True):
    """
        Process a list of requirements to determine how out of date they are.
    """
    requirements = []
    for req_file in req_files:
        requirements.extend(parse_req_file(req_file))
        req_file.close()

    total_time_delta = 0
    for req, version in requirements:
        if print_only:
            if req:
                print("{}=={}".format(req, version))
            else:
                print(version)
        elif verbatim and not req:
            sys.stdout.write(version)
        elif req:
            latest_version, latest_release_date = get_version_and_release_date(req, verbose=(verbosity > 0))
            specified_version, specified_release_date = get_version_and_release_date(req, version, verbose=(verbosity > 0))

            if latest_release_date and specified_release_date:
                time_delta = (latest_release_date - specified_release_date).days
                total_time_delta = total_time_delta + time_delta

                if verbosity:
                    if time_delta > 0:
                        print('{} ({}) is {} days out of date'.format(req, version, time_delta))
                    else:
                        print('{} ({}) is up to date'.format(req, version))

                if latest and latest_version != specified_version:
                    print('{}=={} # Updated from {}'.format(req, latest_version, specified_version))
                elif verbatim and latest_version != specified_version:
                    print('{}=={} # Latest {}'.format(req, specified_version, latest_version))
                elif verbatim:
                    print('{}=={}'.format(req, specified_version))
            else:
                print('{}=={} # Error checking latest version'.format(req, version))

    if verbatim:
        verbatim = "# Generated with piprot {}\n# ".format(VERSION)
    else:
        verbatim = ""
    if total_time_delta > 0:
        print("{}Your requirements are {} days out of date".format(verbatim, total_time_delta))
    else:
        print("{}Looks like you've been keeping up to date, time for a delicious beverage!".format(verbatim))


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
    cli_parser.add_argument('-x', '--verbatim', action='store_true',
                            help='output the full requirements file, with added comments with potential updates')

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

    if len(cli_args.file) > 1 and cli_args.verbatim:
        sys.exit('--verbatim only allowed for single requirements files')

    # call the main function to kick off the real work
    main(req_files=cli_args.file, do_colour=cli_args.colour,
         verbosity=cli_args.verbose, latest=cli_args.latest, verbatim=cli_args.verbatim)

if __name__ == '__main__':
    piprot()
