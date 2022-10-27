#!/usr/bin/env python
"""
piprot - How rotten are your requirements?
"""
from __future__ import print_function

import argparse
import json
import operator
import os
import re
import sys
import time
from datetime import datetime

from piprot.thttp import request, HTTPError

from six.moves import input

from . import __version__
from .providers.github import build_github_url, get_requirements_file_from_url


VERSION = __version__
PYPI_BASE_URL = "https://pypi.org/pypi"


class PiprotVersion(object):
    def __init__(self, version, parts=[]):
        self.parts = [int(re.sub(r"\D", "", p) or 0) for p in parts]
        self.version = version

    def __str__(self):
        return str(self.version)

    def __cmp__(self, other):
        if self.version == other.version:
            return 0

        our_parts = self.parts
        other_parts = other.parts

        # ensure both _parts_ lists have the same length
        while len(our_parts) > len(other_parts):
            other_parts.append(0)

        while len(other_parts) > len(our_parts):
            our_parts.append(0)

        for us, them in zip(self.parts, other.parts):
            if us != them:
                return us - them

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
            re.search(r"(a|b|c|rc|alpha|beta|pre|preview|dev|svn|git)", self.version)
        )


def parse_version(version):
    version = version.strip().replace("-", ".")
    parts = version.split(".")

    if len(parts) > 0 and len(parts) < 6:
        # well, that was (fairly) easy
        return PiprotVersion(version, parts)
    return PiprotVersion(version)


def get_pypi_url(requirement, version=None, base_url=PYPI_BASE_URL):
    """
    Get the PyPI url for a given requirement and optional version number and
    PyPI base URL. The default base url is 'https://pypi.org/pypi'
    """
    return "{base}/{req}/json".format(base=base_url, req=requirement, version=version)


def parse_req_file(req_file, verbatim=False):
    """Take a file and return a dict of (requirement, versions, ignore) based
    on the files requirements specs.
    """
    req_list = []
    requirements = req_file.readlines()
    for requirement in requirements:
        requirement_no_comments = requirement.split("#")[0].strip()

        # if matching requirement line (Thing==1.2.3), update dict, continue
        req_match = re.match(
            r"\s*(?P<package>[^\s\[\]]+)(?P<extras>\[\S+\])?==(?P<version>\S+)",
            requirement_no_comments,
        )
        req_ignore = requirement.strip().endswith("  # norot")

        if req_match:
            req_list.append(
                (req_match.group("package"), req_match.group("version"), req_ignore)
            )
        elif requirement_no_comments.startswith("-r"):
            try:
                base_dir = os.path.dirname(os.path.abspath(req_file.name))
            except AttributeError:
                print(
                    "Recursive requirements are not supported in URL based " "lookups"
                )
                continue

            # replace the -r and ensure there are no leading spaces
            file_name = requirement_no_comments.replace("-r", "").strip()
            new_path = os.path.join(base_dir, file_name)
            try:
                if verbatim:
                    req_list.append((None, requirement, req_ignore))
                req_list.extend(parse_req_file(open(new_path), verbatim=verbatim))
            except IOError:
                print("Failed to import {}".format(file_name))
        elif verbatim:
            req_list.append((None, requirement, req_ignore))
    return req_list


def get_version_and_release_date(
    requirement, version=None, verbose=False, response=None
):
    """Given a requirement and optional version returns a (version, releasedate)
    tuple. Defaults to the latest version. Prints to stdout if verbose is True.
    Optional response argument is the response from PyPI to be used for
    asynchronous lookups.
    """
    if not response:
        url = get_pypi_url(requirement, version)
        response = request(url)

    # see if the url is 404'ing because it has been redirected
    if response.status == 404:
        root_url = url.rpartition("/")[0]
        res = request(root_url, method="HEAD")
        if res.status == 301:
            new_location = res.headers["location"] + "/json"
            response = request(new_location)

    if response.status != 200:
        if version:
            if verbose:
                print(
                    "{} ({}) isn't available on PyPI "
                    "anymore!".format(requirement, version)
                )
        else:
            if verbose:
                print(
                    "{} isn't on PyPI. Check that the project "
                    "still exists!".format(requirement)
                )
        return None, None

    if not response.json:
        if verbose:
            print(
                "Decoding the JSON response for {} ({}) "
                "failed".format(requirement, version)
            )
        return None, None

    response = response.json

    try:
        if version:
            if version in response["releases"]:
                release_date = response["releases"][version][0]["upload_time"]
            else:
                return None, None
        else:
            version = response["info"].get("stable_version")

            if not version:
                versions = {
                    v: parse_version(v)
                    for v in response["releases"].keys()
                    if not parse_version(v).is_prerelease()
                }

                # if we still don't have a version, let's pick up a prerelease one
                if not versions:
                    versions = {
                        v: parse_version(v) for v in response["releases"].keys()
                    }

                if versions:
                    version = max(versions.items(), key=operator.itemgetter(1))[0]
                    release_date = response["releases"][str(version)][0]["upload_time"]
                else:
                    return None, None

        return version, datetime.fromtimestamp(
            time.mktime(time.strptime(release_date, "%Y-%m-%dT%H:%M:%S"))
        )
    except IndexError:
        if verbose:
            print("{} ({}) didn't return a date property".format(requirement, version))
        return None, None


def main(
    req_files,
    verbose=False,
    outdated=False,
    latest=False,
    verbatim=False,
    repo=None,
    path="requirements.txt",
    token=None,
    branch="master",
    url=None,
    delay=None,
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
    - delay specifies a timerange during an outdated package is allowed
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
    max_outdated_time = 0
    results = []

    for req, version, ignore in requirements:
        if verbatim and not req:
            results.append(version)
        elif req:
            results.append(
                {
                    "req": req,
                    "version": version,
                    "ignore": ignore,
                    "latest": request(get_pypi_url(req)),
                    "specified": request(get_pypi_url(req, version)),
                }
            )

    for result in results:
        if isinstance(result, str):
            print(result.replace("\n", ""))
            continue

        if result["ignore"]:
            if verbatim:
                print("{}=={}  # norot".format(result["req"], result["version"]))
            else:
                print("Ignoring updates for {}. ".format(result["req"]))
            continue

        req = result["req"]
        version = result["version"]

        latest_version, latest_release_date = get_version_and_release_date(
            req, verbose=verbose, response=result["latest"]
        )
        specified_version, specified_release_date = get_version_and_release_date(
            req, version, response=result["specified"]
        )

        if latest_release_date and specified_release_date:
            time_delta = (latest_release_date - specified_release_date).days
            total_time_delta = total_time_delta + time_delta
            max_outdated_time = max(time_delta, max_outdated_time)

            if verbose:
                if time_delta > 0:
                    print(
                        "{} ({}) is {} days out of date. "
                        "Latest is {}".format(req, version, time_delta, latest_version)
                    )
                elif version != latest_version:
                    print(
                        "{} ({}) is out of date. "
                        "Latest is {}".format(req, version, latest_version)
                    )
                elif not outdated:
                    print("{} ({}) is up to date".format(req, version))

            if latest and latest_version != specified_version:
                print(
                    "{}=={}  # Updated from {}".format(
                        req, latest_version, specified_version
                    )
                )
            elif verbatim and latest_version != specified_version:
                print(
                    "{}=={}  # Latest {}".format(req, specified_version, latest_version)
                )
            elif verbatim:
                print("{}=={}".format(req, specified_version))

        elif verbatim:
            print("{}=={}  # Error checking latest version".format(req, version))

    verbatim_str = ""
    if verbatim:
        verbatim_str = "# Generated with piprot {}\n# ".format(VERSION)

    if total_time_delta > 0 and delay is None:
        print(
            "{}Your requirements are {} "
            "days out of date".format(verbatim_str, total_time_delta)
        )
        sys.exit(1)
    elif delay is not None and max_outdated_time > int(delay):
        print(
            "{}At least one of your dependencies is {} "
            "days out of date which is more than the allowed"
            "{} days.".format(verbatim_str, max_outdated_time, delay)
        )
        sys.exit(1)
    elif delay is not None and max_outdated_time <= int(delay):
        print(
            "{}All of your dependencies are at most {} "
            "days out of date.".format(verbatim_str, delay)
        )
    else:
        print(
            "{}Looks like you've been keeping up to date, "
            "time for a delicious beverage!".format(verbatim_str)
        )


def piprot():
    """Parse the command line arguments and jump into the piprot() function
    (unless the user just wants the post request hook).
    """
    cli_parser = argparse.ArgumentParser(
        epilog="Here's hoping your requirements are nice and fresh!"
    )
    cli_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbosity, can be supplied more than once "
        "(enabled by default, use --quiet to disable)",
    )
    cli_parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="print the lastest available version for out " "of date requirements",
    )
    cli_parser.add_argument(
        "-x",
        "--verbatim",
        action="store_true",
        help="output the full requirements file, with "
        "added comments with potential updates",
    )
    cli_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="be a little less verbose with the output " "(<0.3 behaviour)",
    )
    cli_parser.add_argument(
        "-o", "--outdated", action="store_true", help="only list outdated requirements"
    )

    cli_parser.add_argument(
        "-g",
        "--github",
        help="Test the requirements from a GitHub repo. "
        "Requires that a `requirements.txt` file "
        "exists in the root of the repository.",
    )

    cli_parser.add_argument(
        "-b",
        "--branch",
        help="The branch to test requirements from, used with "
        "the Github URL support.",
    )

    cli_parser.add_argument(
        "-t",
        "--token",
        help="Github personal access token to be used with " "the Github URL support.",
    )

    cli_parser.add_argument(
        "-p", "--path", help="Path to requirements file in remote repository."
    )

    cli_parser.add_argument(
        "-d",
        "--delay",
        help="Delay before an outdated package triggers an error."
        "(in days, default to 1).",
    )

    cli_parser.add_argument("-u", "--url", help="URL to requirements file.")

    # if there is a requirements.txt file, use it by default. Otherwise print
    # usage if there are no arguments.
    nargs = "+"

    if (
        "--github" in sys.argv
        or "-g" in sys.argv
        or "-u" in sys.argv
        or "--url" in sys.argv
    ):
        nargs = "*"

    default = None
    if os.path.isfile("requirements.txt"):
        nargs = "*"
        default = [open("requirements.txt")]

    cli_parser.add_argument(
        "file",
        nargs=nargs,
        type=argparse.FileType(),
        default=default,
        help="requirements file(s), use " "`-` for stdin",
    )

    cli_args = cli_parser.parse_args()

    if len(cli_args.file) > 1 and cli_args.verbatim:
        sys.exit("--verbatim only allowed for single requirements files")

    verbose = True
    if cli_args.quiet:
        verbose = False
    elif cli_args.verbatim:
        verbose = False

    # call the main function to kick off the real work
    main(
        req_files=cli_args.file,
        verbose=verbose,
        outdated=cli_args.outdated,
        latest=cli_args.latest,
        verbatim=cli_args.verbatim,
        repo=cli_args.github,
        branch=cli_args.branch,
        path=cli_args.path,
        token=cli_args.token,
        url=cli_args.url,
        delay=cli_args.delay,
    )


if __name__ == "__main__":
    piprot()
