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

VERSION = "0.7.0"
PYPI_BASE_URL = 'https://pypi.python.org/pypi'

USE_NOTIFY = True
NOTIFY_URL = 'https://piprot.io/notify/'


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


def notify_requirements(email_address, requirements, reset):
    return requests.post(NOTIFY_URL, data=json.dumps({
                                        'requirements': requirements,
                                        'email': email_address,
                                        'reset': reset}),
                                     headers={
                                        'Content-type': 'application/json'
                                     }).json()


def get_version_and_release_date(requirement, version=None, verbose=False, release_data=None):
    response = None
    if release_data:
        if requirement in release_data.keys():
            if version:
                return release_data[requirement]['release'], datetime.fromtimestamp(time.mktime(
                                time.strptime(release_data[requirement]['released_at'], '%Y-%m-%dT%H:%M:%S')
                            ))
            else:
                return release_data[requirement]['latest'], datetime.fromtimestamp(time.mktime(
                                time.strptime(release_data[requirement]['latest_released_at'], '%Y-%m-%dT%H:%M:%S')
                            ))
    try:
        url = get_pypi_url(requirement, version)
        response = requests.get(url)

        # see if the url is 404'ing because it has been redirected
        if response.status_code == 404:
            root_url = url.rpartition('/')[0]
            res = requests.head(root_url)
            if res.status_code == 301:
                new_location = res.headers['location'] + '/json'
                response = requests.get(new_location)

        response = response.json()
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
    except ValueError:
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


def main(req_files=[], verbose=False, outdated=False, latest=False,
         verbatim=False, print_only=False, notify='', reset=False):
    requirements = []
    for req_file in req_files:
        requirements.extend(parse_req_file(req_file, verbatim=verbatim))
        req_file.close()

    total_time_delta = 0

    release_data = None
    if notify and USE_NOTIFY:
        # Do notify and exit asap
        only_requirements = {}
        for req, version in requirements:
            if req:
                only_requirements[req] = version
        response = notify_requirements(notify, only_requirements, reset)

        if response['status'] == 'OK':
            print('Your requirements have been uploaded to piprot.io and {} ' \
                  'will be notified when new version are released. You are ' \
                  'tracking {} packages.'.format(response['email'],
                                                 response['package_count']))
            return
        else:
            print('Something went wrong while uploading to piprot.io, please ' \
                  'file a bug report if this continues')
            return

    for req, version in requirements:
        if print_only:
            if req:
                print("{}=={}".format(req, version))
            else:
                print(version)
        elif verbatim and not req:
            sys.stdout.write(version)
        elif req:
            latest_version, latest_release_date = get_version_and_release_date(req, verbose=verbose, release_data=release_data)
            specified_version, specified_release_date = get_version_and_release_date(req, version, verbose=verbose, release_data=release_data)

            if latest_release_date and specified_release_date:
                time_delta = (latest_release_date - specified_release_date).days
                total_time_delta = total_time_delta + time_delta

                if verbose:
                    if time_delta > 0:
                        print('{} ({}) is {} days out of date. Latest is {}'.format(req, version, time_delta, latest_version))
                    elif not outdated:
                        print('{} ({}) is up to date'.format(req, version))

                if latest and latest_version != specified_version:
                    print('{}=={} # Updated from {}'.format(req, latest_version, specified_version))
                elif verbatim and latest_version != specified_version:
                    print('{}=={} # Latest {}'.format(req, specified_version, latest_version))
                elif verbatim:
                    print('{}=={}'.format(req, specified_version))
            elif verbatim:
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
    cli_parser.add_argument('-v', '--verbose', action='store_true',
                            help='verbosity, can be supplied more than once (enabled by default, use --quiet to disable)')
    cli_parser.add_argument('-l', '--latest', action='store_true',
                            help='print the lastest available version for out of date requirements')
    cli_parser.add_argument('-x', '--verbatim', action='store_true',
                            help='output the full requirements file, with added comments with potential updates')
    cli_parser.add_argument('-q', '--quiet', action='store_true',
                            help='be a little less verbose with the output (<0.3 behaviour)')
    cli_parser.add_argument('-o', '--outdated', action='store_true',
                            help='only list outdated requirements')

    cli_parser.add_argument('-n', '--notify',
                            help='submit requirements to piprot notify for weekly')
    cli_parser.add_argument('-r', '--reset', action='store_true',
                            help='reset your piprot notify subscriptions, will clear all package subscriptions before adding these requirements')

    # if there is a requirements.txt file, use it by default. Otherwise print
    # usage if there are no arguments.
    nargs = '+'
    default = None
    if os.path.isfile('requirements.txt'):
        nargs = '*'
        default = [open('requirements.txt')]

    cli_parser.add_argument('file', nargs=nargs, type=argparse.FileType(),
                            default=default, help='requirements file(s), use `-` for stdin')

    cli_args = cli_parser.parse_args()

    if len(cli_args.file) > 1 and cli_args.verbatim:
        sys.exit('--verbatim only allowed for single requirements files')

    # call the main function to kick off the real work
    verbose = True
    if cli_args.quiet:
        verbose = False
    elif cli_args.verbatim:
        verbose = False

    main(req_files=cli_args.file, verbose=verbose, outdated=cli_args.outdated,
         latest=cli_args.latest, verbatim=cli_args.verbatim, print_only=False,
         notify=cli_args.notify, reset=cli_args.reset)


if __name__ == '__main__':
    piprot()
