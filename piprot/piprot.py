#!/usr/bin/env python
"""
piprot - How rotten are your requirements?
"""
from __future__ import print_function

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from requests_futures.sessions import FuturesSession

from pkg_resources import parse_version
from six.moves import input

from . import __version__
from .providers.github import build_github_url, get_requirements_file_from_url


VERSION = __version__
PYPI_BASE_URL = 'https://pypi.python.org/pypi'
#PYPI_BASE_URL = 'https://warehouse.python.org/pypi'

USE_NOTIFY = True
NOTIFY_URL = 'https://piprot.io/notify/'


def get_pypi_url(requirement, version=None, base_url=PYPI_BASE_URL):
    """
    Get the PyPI url for a given requirement and optional version number and
    PyPI base URL. The default base url is 'https://pypi.python.org/pypi'
    """
    if version:
        return '{base}/{req}/{version}/json'.format(base=base_url,
                                                    req=requirement,
                                                    version=version)
    else:
        return '{base}/{req}/json'.format(base=base_url, req=requirement)


def parse_req_file(req_file, verbatim=False):
    """Take a file and return a dict of (requirement, versions) based
    on the files requirements specs.
    """
    req_list = []
    requirements = req_file.readlines()
    for requirement in requirements:
        requirement_no_comments = requirement.split('#')[0].strip()

        # if matching requirement line (Thing==1.2.3), update dict, continue
        req_match = re.match(r'\s*(?P<package>\S+)==(?P<version>\S+)',
                             requirement_no_comments)
        if req_match:
            req_list.append((req_match.group('package'),
                             req_match.group('version')))
        elif requirement_no_comments.startswith('-r'):
            try:
                base_dir = os.path.dirname(os.path.abspath(req_file.name))
            except AttributeError:
                print('Recursive requirements are not supported in URL based lookups')
                continue

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


def get_version_and_release_date(requirement, version=None,
                                 verbose=False, response=None):
    """Given a requirement and optional version returns a (version, releasedate)
    tuple. Defaults to the latest version. Prints to stdout if verbose is True.
    Optional response argument is the response from PyPI to be used for
    asyncronous lookups.
    """
    try:
        if not response:
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
                print ('{} ({}) isn\'t available on PyPI '
                       'anymore!'.format(requirement, version))
        else:
            if verbose:
                print ('{} isn\'t on PyPI. Check that the project '
                       'still exists!'.format(requirement))
        return None, None
    except ValueError:
        if verbose:
            print ('Decoding the JSON response for {} ({}) '
                   'failed'.format(requirement, version))
        return None, None

    try:
        if version:
            release_date = response['releases'][version][0]['upload_time']
        else:
            version = response['info']['stable_version']

            if not version:
                versions = {parse_version(v): v for v in response['releases'].keys() if not parse_version(v).is_prerelease}
                version = versions[max(versions.keys())]
                release_date = response['releases'][str(version)][0]['upload_time']

        return version, datetime.fromtimestamp(time.mktime(
            time.strptime(release_date, '%Y-%m-%dT%H:%M:%S')
        ))
    except IndexError:
        if verbose:
            print ('{} ({}) didn\'t return a date property'.format(requirement,
                                                                   version))
        return None, None


def main(req_files, verbose=False, outdated=False, latest=False,
         verbatim=False, notify='', reset=False, repo=None, path='requirements.txt',
         token=None, branch='master', url=None):
    """Given a list of requirements files reports which requirements are out
    of date.

    Everything is rather somewhat obvious:
    - verbose makes things a little louder
    - outdated forces piprot to only report out of date packages
    - latest outputs the requirements line with the latest version
    - verbatim outputs the requirements file as-is - with comments showing the
      latest versions (can be used with latest to output the latest with the old
      version in the comment)
    - notify is a string that should be an email address to upload to piprot.io
    - reset goes with the notification to decide whether to reset the packages
      subscribed to.
    """
    requirements = []

    if repo:
        github_url = build_github_url(repo, branch, path, token)
        req_file = get_requirements_file_from_url(github_url)
        requirements.extend(parse_req_file(req_file))
    elif url:
        req_file = get_requirements_file_from_url(url)
        requirements.extend(parse_req_file(req_file))
    else:
        for req_file in req_files:
            requirements.extend(parse_req_file(req_file, verbatim=verbatim))
            req_file.close()

    total_time_delta = 0

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

    session = FuturesSession()
    results = []

    for req, version in requirements:
        if verbatim and not req:
            results.append(version)
        elif req:
            results.append({
                'req': req,
                'version': version,
                'latest': session.get(get_pypi_url(req)),
                'specified': session.get(get_pypi_url(req, version))
            })

    for result in results:
        if isinstance(result, str):
            print(result.replace('\n', ''))
            continue

        req = result['req']
        version = result['version']

        latest_version, latest_release_date = \
                        get_version_and_release_date(req, verbose=verbose,
                                                     response=result['latest']\
                                                              .result())
        specified_version, specified_release_date = \
                           get_version_and_release_date(req, version,
                                                        response=result[\
                                                        'specified'].result())

        if latest_release_date and specified_release_date:
            time_delta = (latest_release_date - specified_release_date).days
            total_time_delta = total_time_delta + time_delta

            if verbose:
                if time_delta > 0:
                    print('{} ({}) is {} days out of date. '
                          'Latest is {}'.format(req, version, time_delta,
                                                latest_version))
                elif version != latest_version:
                    print('{} ({}) is out of date. '
                          'Latest is {}'.format(req, version, latest_version))
                elif not outdated:
                    print('{} ({}) is up to date'.format(req, version))

            if latest and latest_version != specified_version:
                print('{}=={} # Updated from {}'.format(req, latest_version,
                                                        specified_version))
            elif verbatim and latest_version != specified_version:
                print('{}=={} # Latest {}'.format(req, specified_version,
                                                  latest_version))
            elif verbatim:
                print('{}=={}'.format(req, specified_version))

        elif verbatim:
            print('{}=={} # Error checking latest version'.format(req, version))

    verbatim_str = ""
    if verbatim:
        verbatim_str = "# Generated with piprot {}\n# ".format(VERSION)

    if total_time_delta > 0:
        print("{}Your requirements are {} "
              "days out of date".format(verbatim_str, total_time_delta))
        sys.exit(1)
    else:
        print("{}Looks like you've been keeping up to date, "
              "time for a delicious beverage!".format(verbatim_str))


def output_post_commit(email=None, path=None):
    """Asks for email address and filepath from stdin and outputs a sample
    post-commit hook to stdout
    """
    email = email or input('Your email address:')
    path = path or input('Full path to requirements'
                          '[{}/requirements.txt]:'.format(os.getcwd()))

    if not path:
        path = os.path.join(os.getcwd(), 'requirements.txt')

    print("""#!/bin/sh
#
# piprot post-commit hook to send your requirements file to piprot.io
# and ensure you're always getting the latest notification
#
# Future enhancement: only run this for commits to a specific branch
#

piprot --notify={email} {path}""".format(email=email, path=path))


def notify_requirements(email_address, requirements, reset=False):
    """Given and email address, list of requirements and optional reset
    argument subscribes the user to updates from piprot.io. The reset
    argument is used to reset the subscription to _just_ these packages.
    """
    return requests.post(NOTIFY_URL,
                         data=json.dumps({'requirements': requirements,
                                          'email': email_address,
                                          'reset': reset}),
                         headers={'Content-type': 'application/json'}).json()


def piprot():
    """Parse the command line arguments and jump into the piprot() function
    (unless the user just wants the post request hook).
    """
    cli_parser = argparse.ArgumentParser(
        epilog="Here's hoping your requirements are nice and fresh!"
    )
    cli_parser.add_argument('-v', '--verbose', action='store_true',
                            help='verbosity, can be supplied more than once '
                                 '(enabled by default, use --quiet to disable)')
    cli_parser.add_argument('-l', '--latest', action='store_true',
                            help='print the lastest available version for out '
                                 'of date requirements')
    cli_parser.add_argument('-x', '--verbatim', action='store_true',
                            help='output the full requirements file, with '
                                 'added comments with potential updates')
    cli_parser.add_argument('-q', '--quiet', action='store_true',
                            help='be a little less verbose with the output '
                                 '(<0.3 behaviour)')
    cli_parser.add_argument('-o', '--outdated', action='store_true',
                            help='only list outdated requirements')

    cli_parser.add_argument('-n', '--notify',
                            help='submit requirements to piprot notify for '
                                 'weekly')
    cli_parser.add_argument('-r', '--reset', action='store_true',
                            help='reset your piprot notify subscriptions, will '
                                 'clear all package subscriptions before '
                                 'adding these requirements')

    cli_parser.add_argument('-c', '--notify-post-commit', action='store_true',
                            help='output a sample post-commit hook to send '
                                 'requirements to piprot.io after every commit')

    cli_parser.add_argument('-g', '--github',
                            help='Test the requirements from a GitHub repo. '
                                 'Requires that a `requirements.txt` file '
                                 'exists in the root of the repository.')

    cli_parser.add_argument('-b', '--branch',
                            help='The branch to test requirements from, used with '
                                 'the Github URL support.')

    cli_parser.add_argument('-t', '--token',
                            help='Github personal access token to be used with '
                                 'the Github URL support.')

    cli_parser.add_argument('-p', '--path',
                            help='Path to requirements file in remote repository.')

    cli_parser.add_argument('-u', '--url',
                            help='URL to requirements file.')

    # if there is a requirements.txt file, use it by default. Otherwise print
    # usage if there are no arguments.
    nargs = '+'

    if '--github' in sys.argv or '-g' in sys.argv or '-u' in sys.argv or '--url' in sys.argv:
        nargs = "*"

    default = None
    if os.path.isfile('requirements.txt'):
        nargs = "*"
        default = [open('requirements.txt')]

    cli_parser.add_argument('file', nargs=nargs, type=argparse.FileType(),
                            default=default, help='requirements file(s), use '
                                                  '`-` for stdin')

    cli_args = cli_parser.parse_args()

    if len(cli_args.file) > 1 and cli_args.verbatim:
        sys.exit('--verbatim only allowed for single requirements files')

    verbose = True
    if cli_args.quiet:
        verbose = False
    elif cli_args.verbatim:
        verbose = False

    if cli_args.notify_post_commit:
        output_post_commit()
        return

    # call the main function to kick off the real work
    main(req_files=cli_args.file, verbose=verbose, outdated=cli_args.outdated,
         latest=cli_args.latest, verbatim=cli_args.verbatim,
         notify=cli_args.notify, reset=cli_args.reset, repo=cli_args.github,
         branch=cli_args.branch, path=cli_args.path, token=cli_args.token,
         url=cli_args.url)


if __name__ == '__main__':
    piprot()
