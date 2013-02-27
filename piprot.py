#!/usr/bin/env python
from datetime import datetime
from clint import args
import json
import time
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import urllib2
import clint
import sys


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


def load_requirements(req_file, lint, colour=TextColours(False)):
    """
        Take a file and return a dict of (requirement, versions)
        based on the requirements files
    """
    req_dict = {}
    requirements = req_file.readlines()

    for requirement in requirements:
        requirement = requirement.replace('\n', '').strip().split(' ')[0]
        if requirement and requirement[0] not in ['#', '-'] and 'git' not in requirement:
            try:
                requirement, version = requirement.split('==')
                req_dict[requirement] = version
            except ValueError:
                # what are you doing!
                if lint:
                    print '%s%s doesn\'t have a version number%s' % \
                                (colour.FAIL, requirement, colour.ENDC)

    return req_dict


def get_release_date(requirement, version=None, colour=TextColours(False)):
    j = None
    try:
        if version:
            j = urllib2.urlopen('https://pypi.python.org/pypi/%s/%s/json' % (requirement, version))
        else:
            j = urllib2.urlopen('https://pypi.python.org/pypi/%s/json' % (requirement))
    except urllib2.HTTPError:
        if version:
            print '%s%s (%s) isn\'t available on PyPi anymore!%s' % \
                    (colour.FAIL, requirement, version, colour.ENDC)
        else:
            print '%s%s isn\'t even on PyPi. Check that the project still exists!%s' % \
                    (colour.FAIL, requirement, colour.ENDC)
        return None

    try:
        j = json.load(j)
        d = j['urls'][0]['upload_time']
        return datetime.fromtimestamp(time.mktime(time.strptime(d, '%Y-%m-%dT%H:%M:%S')))
    except IndexError:
        print '%s%s (%s) didn\'t return a date property%s' % (colour.FAIL, requirement, version, colour.ENDC)

if __name__ == '__main__':
    # so, you need help do you?
    if '--help' in args.all:
        print 'piprot is a handle little tool that tells you just how rotten your ' + \
                    'requirements are!'
        print 'Turns out, they\'re pretty damn rotten!\n'
        print 'Usage:\tpiprot <requirements-file> [OPTIONS]'
        print '\tpip freeze | piprot [OPTIONS]'
        print '\nAvailable options: '
        print '  -c\t\tPretty colours'
        print '  -l --lint\tEnable linting of your requirements file'
        print '  -v\t\tVerbose output, you\'ll normally want this'
        sys.exit()

    # use the first file as our requirements file
    req_file = None

    # optionally, enable colour output
    colour = TextColours(False)
    if '-c' in args.all:
        colour.enable()

    c = clint.piped_in()
    try:
        if c:
            # some idiot piped something in
            req_file = StringIO.StringIO(c)
        else:
            # the first file is all that matters. Yep.
            # multi file support coming in 2.0
            req_file = open(args.files[0])

    except IndexError:
        print '%sYou need to supply at least one filename%s' % (colour.FAIL, colour.ENDC)
        sys.exit()

    # are we being annoyingly verbose?
    verbose = False
    if '-v' in args.all:
        verbose = True

    # wanna add a little linting (this is in early stages)
    lint = False
    if '--lint' in args.all or '-l' in args.all:
        lint = True

    if req_file:
        requirements = load_requirements(req_file, lint, colour)
        total_time_delta = 0
        for req, version in requirements.items():
            latest_version = get_release_date(req, colour=colour)
            specified_version = get_release_date(req, version, colour=colour)

            if latest_version and specified_version:
                time_delta = (latest_version - specified_version).days
                total_time_delta = total_time_delta + time_delta

                if verbose:
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
