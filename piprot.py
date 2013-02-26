#!/usr/bin/env python
from clint.textui import puts, colored
from datetime import datetime
from clint import args
import json, time
import StringIO
import urllib2
import clint
import sys

def load_requirements(req_file, lint=False):
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
                    puts(colored.red('%s doesn\'t have a version number' % requirement))

    return req_dict

def get_release_date(requirement, version=None):
    j = None
    try:
        if version:
            j = urllib2.urlopen('https://pypi.python.org/pypi/%s/%s/json' % (requirement, version))
        else:
            j = urllib2.urlopen('https://pypi.python.org/pypi/%s/json' % (requirement))
    except urllib2.HTTPError:
        if version:
            puts(colored.red('%s (%s) isn\'t available on PyPi anymore!' % (requirement, version)))
        else:
            puts(colored.red('%s isn\'t even on PyPi. Check that the project still exists!' % (requirement)))
        return None
    try:
        j = json.load(j)
        d = j['urls'][0]['upload_time']
        return datetime.fromtimestamp(time.mktime(time.strptime(d, '%Y-%m-%dT%H:%M:%S')))
    except IndexError:
        puts(colored.red('%s (%s) didn\'t return a date property' % (requirement, version)))

if __name__ == '__main__':
    # use the first file as our requirements file
    req_file = None

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
        puts(colored.red('You need to supply at least one filename'))
        sys.exit()

    # are we being annoyingly verbose?
    verbose = False
    if '-v' in args.all:
        verbose = True

    # wanna add a little linting (this is in early stages)
    lint = False
    if '--lint' in args.all:
        lint = True

    if req_file:
        requirements = load_requirements(req_file, lint)
        total_time_delta = 0
        for req, version in requirements.items():
            latest_version = get_release_date(req)
            specified_version = get_release_date(req, version)

            if latest_version and specified_version:
                time_delta = (latest_version - specified_version).days
                total_time_delta = total_time_delta + time_delta

                if verbose:
                    if time_delta > 0:
                        puts(colored.yellow('%s (%s) is %s days out of date' % (req, version, time_delta)))
                    else:
                        puts(colored.green('%s (%s) is up to date' % (req, version)))
        if total_time_delta > 0:
            puts(colored.red("Your requirements are %s days out of date" % total_time_delta))
        else:
            puts(colored.green("Looks like you've been keeping up to date, better go back to taming that beard!"))