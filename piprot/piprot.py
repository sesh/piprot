#!/usr/bin/env python
"""
piprot - How rotten are your requirements?
"""
from __future__ import print_function

import argparse
import os
import re
import sys
import yaml
from datetime import datetime

import requests
from requests_futures.sessions import FuturesSession

from six.moves import input

from . import __version__
from .providers.github import build_github_url, get_requirements_file_from_url
from .providers.conda import package_info

try:
    from itertools import zip_longest as zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

VERSION = __version__
PYPI_BASE_URL = 'https://pypi.python.org/pypi'


class PiprotVersion(object):

    def __init__(self, version, parts=None, buildlabel='', release_date=None):
        self.parts = [part.strip() for part in parts or []]
        self.version = version
        self.buildlabel = buildlabel
        self.release_date = release_date

    def __str__(self):
        if self.buildlabel:
            return str(self.conda_buildversion)
        return str(self.version)

    def __cmp__(self, other):
        if self.is_prerelease() == other.is_prerelease():
            for us, them in zip_longest(self.parts, other.parts, fillvalue='0'):
                if us != them:
                    if us.isdigit() and them.isdigit():
                        return cmp(int(us), int(them))
                    return cmp(us, them)

            if self.buildlabel != other.buildlabel:
                return cmp(self.buildlabel, other.buildlabel)

        if self.is_prerelease():
            return -1

        if other.is_prerelease():
            return 1

        # um, yeah
        return 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def is_prerelease(self):
        return bool(
            re.search(
                r'(a|b|c|rc|alpha|beta|pre|preview|dev|svn|git)',
                self.version
            )
        )

    @property
    def conda_buildversion(self):
        return self.version + "=" + self.buildlabel


def cmp(a, b):
    return (a > b) - (a < b)


def parse_version(version, release_date=None, buildlabel='0'):
    version = version.strip().replace('-', '.')
    parts = version.split('.')

    if len(parts) > 0 and len(parts) < 6:
        # well, that was (fairly) easy
        return PiprotVersion(version, parts, buildlabel=buildlabel, release_date=release_date)
    return PiprotVersion(version, buildlabel=buildlabel, release_date=release_date)


def get_version(provider, requirement, version, conda_basepath=None, verbose=False):
    """
    Get the versions for a requirement.

    :param prodiver: the name of the dependency provider, can be either pip or conda
    :param version: the current version
    :param verbose: print if versions are not available
    :returns: the current version, current releasedate, latest version, latest releasedate
    """

    if provider == "pip":
        releases, latest_stable = fetch_pypi_versions(requirement, verbose)
    elif provider == "conda":
        releases, latest_stable = fetch_conda_versions(requirement, conda_basepath, verbose)
    else:
        raise RuntimeError("Unknown provider '%s'", provider)

    if version in releases:
        return version, releases[version].release_date, \
            latest_stable, releases[latest_stable].release_date

    elif verbose:
        print('{} ({}) isn\'t available on anymore!'.format(requirement, version))

    return None, None, None, None


def fetch_pypi_versions(requirement, verbose=False, base_url=PYPI_BASE_URL):
    """
    Get the PyPI url for a given requirement and optional version number and
    PyPI base URL. The default base url is 'https://pypi.python.org/pypi'
    """
    try:
        url = '{base}/{req}/json'.format(base=base_url, req=requirement)
        response = requests.get(url)

        # see if the url is 404'ing because it has been redirected
        if response.status_code == 404:
            root_url = url.rpartition('/')[0]
            res = requests.head(root_url)
            if res.status_code == 301:
                new_location = res.headers['location'] + '/json'
                response = requests.get(new_location)

        def parse_date(value):
            return datetime.strptime(value[0]['upload_time'], '%Y-%m-%dT%H:%M:%S')

        pypi_response = response.json()
        releases = {
            v: parse_version(v, parse_date(value)) for v, value in pypi_response['releases'].items() if value
        }
        latest_stable = pypi_response['info'].get('stable_version')
        if not latest_stable:
            # did not find stable version, use max defined by PiprotVersion cmp
            latest_stable = max(releases.values()).version

        return releases, latest_stable

    except requests.HTTPError:
        if verbose:
            print('{} isn\'t on PyPI. Check that the project '
                  'still exists!'.format(requirement))
    except ValueError:
        if verbose:
            print('Decoding the JSON response for {} '
                  'failed'.format(requirement))

    return None, None


def fetch_conda_versions(requirement, conda_basepath=None, verbose=False):
    conda_response = package_info(requirement, conda_basepath)

    def parse_date(release_date):
        return datetime.strptime(release_date, '%Y-%m-%d')

    versions = [parse_version(v['version'], parse_date(v['date']), v['build']) for v in conda_response[requirement]]

    version_dict = {}
    for v in versions:
        version_dict[v.conda_buildversion] = v
        version_dict[v.version] = max(v, version_dict.get(v.version, v))

    max_version = max(versions).conda_buildversion
    return version_dict, max_version


def parse_file(file, verbatim=False):
    if file.name.endswith(".yml"):
        return parse_conda_file(file, verbatim)
    return parse_req_file(file, verbatim)


def parse_req_file(req_file, verbatim=False):
    """Take a file and return a dict of (requirement, versions, ignore) based
    on the files requirements specs.
    """
    req_list = []

    try:
        for requirement in req_file:
            requirement_no_comments = requirement.split('#')[0].strip()

            # if matching requirement line (Thing==1.2.3), update dict, continue
            req_match = re.match(
                r'\s*(?P<package>[^\s\[\]]+)(?P<extras>\[\S+\])?==(?P<version>\S+)',
                requirement_no_comments
            )
            req_ignore = requirement.strip().endswith('  # norot')

            if req_match:
                req_list.append(("pip",
                                 req_match.group('package'),
                                 req_match.group('version'),
                                 req_ignore))
            elif requirement_no_comments.startswith('-r'):
                try:
                    base_dir = os.path.dirname(os.path.abspath(req_file.name))
                except AttributeError:
                    print(
                        'Recursive requirements are not supported in URL based '
                        'lookups'
                    )
                    continue

                # replace the -r and ensure there are no leading spaces
                file_name = requirement_no_comments.replace('-r', '').strip()
                new_path = os.path.join(base_dir, file_name)
                try:
                    if verbatim:
                        req_list.append(("pip", None, requirement, req_ignore))
                    req_list.extend(
                        parse_req_file(
                            open(new_path),
                            verbatim=verbatim
                        )
                    )
                except IOError:
                    print('Failed to import {}'.format(file_name))
            elif verbatim:
                req_list.append(("pip", None, requirement, req_ignore))
        return req_list

    finally:
        req_file.close()


def parse_conda_file(conda_file, verbatim=False):
    """Take a file an return a dict of (requirement, versions, ignore) based
    on the conda environment specs.
    """
    req_list = []

    try:
        parsed_environment = yaml.load(conda_file)
        for item in parsed_environment['dependencies']:
            if isinstance(item, str):
                package, version = item.split("=", 1)
                req_list.append(("conda", package, version, False))

            elif isinstance(item, dict) and 'pip' in item:
                for pipitem in item['pip']:
                    package, version = pipitem.split("==", 1)
                    req_list.append(("pip", package, version, False))

        return req_list
    finally:
        conda_file.close()


def main(
    req_files,
    verbose=False,
    outdated=False,
    latest=False,
    verbatim=False,
    repo=None,
    path='requirements.txt',
    conda_basepath=None,
    token=None,
    branch='master',
    url=None
):
    """Given a list of requirements files reports which requirements are out
    of date.

    Everything is rather somewhat obvious:
    - verbose makes things a little louder
    - outdated forces piprot to only report out of date packages
    - latest outputs the requirements line with the latest version
    - verbatim outputs the requirements file as-is - with comments showing the
      latest versions (can be used with latest to output the latest with the
      old version in the comment)
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
            requirements.extend(parse_file(req_file, verbatim=verbatim))

    total_time_delta = 0
    results = []

    for provider, req, version, ignore in requirements:
        if verbatim and not req:
            results.append(version)
        elif req:
            results.append({
                'req': req,
                'version': version,
                'ignore': ignore,
                'specified_latest': get_version(provider, req, version, conda_basepath, verbose=verbose)
            })

    for result in results:
        if isinstance(result, str):
            print(result.replace('\n', ''))
            continue

        if result['ignore']:
            if verbatim:
                print('{}=={}  # norot'.format(result['req'], result['version']))
            else:
                print('Ignoring updates for {}. '.format(result['req']))
            continue

        req = result['req']
        version = result['version']

        (specified_version, specified_release_date,
         latest_version, latest_release_date) = result['specified_latest']

        if latest_release_date and specified_release_date:
            time_delta = (latest_release_date - specified_release_date).days
            total_time_delta = total_time_delta + time_delta

            if verbose:
                if time_delta != 0:
                    print('{} ({}) is {} days out of date. '
                          'Latest is {}'.format(req, version, time_delta,
                                                latest_version))
                elif version != latest_version:
                    print('{} ({}) is out of date. '
                          'Latest is {}'.format(req, version, latest_version))
                elif not outdated:
                    print('{} ({}) is up to date'.format(req, version))

            if latest and latest_version != specified_version:
                print('{}=={}  # Updated from {}'.format(req, latest_version,
                                                         specified_version))
            elif verbatim and latest_version != specified_version:
                print('{}=={}  # Latest {}'.format(req, specified_version,
                                                   latest_version))
            elif verbatim:
                print('{}=={}'.format(req, specified_version))

        elif verbatim:
            print(
                '{}=={}  # Error checking latest version'.format(req, version)
            )

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


def piprot():
    """Parse the command line arguments and jump into the piprot() function
    (unless the user just wants the post request hook).
    """
    cli_parser = argparse.ArgumentParser(
        epilog="Here's hoping your requirements are nice and fresh!"
    )
    cli_parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='verbosity, can be supplied more than once '
             '(enabled by default, use --quiet to disable)'
    )
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

    cli_parser.add_argument('-g', '--github',
                            help='Test the requirements from a GitHub repo. '
                                 'Requires that a `requirements.txt` file '
                                 'exists in the root of the repository.')

    cli_parser.add_argument(
        '-b', '--branch',
        help='The branch to test requirements from, used with '
             'the Github URL support.')

    cli_parser.add_argument(
        '-t', '--token',
        help='Github personal access token to be used with '
             'the Github URL support.')

    cli_parser.add_argument(
        '-p', '--path',
        help='Path to requirements file in remote repository.')

    cli_parser.add_argument(
        '-c', '--conda_path',
        help='Path to conda installation to use.')

    cli_parser.add_argument('-u', '--url',
                            help='URL to requirements file.')

    # if there is a requirements.txt file, use it by default. Otherwise print
    # usage if there are no arguments.
    nargs = '+'

    if (
        '--github' in sys.argv
        or '-g' in sys.argv
        or '-u' in sys.argv
        or '--url' in sys.argv
    ):
        nargs = "*"

    default = []
    if os.path.isfile('requirements.txt'):
        nargs = "*"
        default.append(open('requirements.txt'))

    if os.path.isfile("environment.yml"):
        nargs = "*"
        default.append(open('environment.yml'))

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

    # call the main function to kick off the real work
    main(req_files=cli_args.file, verbose=verbose, outdated=cli_args.outdated,
         latest=cli_args.latest, verbatim=cli_args.verbatim,
         repo=cli_args.github, branch=cli_args.branch, path=cli_args.path,
         conda_basepath=cli_args.conda_path, token=cli_args.token, url=cli_args.url)


if __name__ == '__main__':
    piprot()
