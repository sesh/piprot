#!/usr/bin/env python
from clint.textui import puts, colored
from datetime import datetime
from clint import args
import urllib2
import json
import time

def load_requirements(filename, lint=True):
    """
        Take a filename and return a dict of (requirement, versions)
        based on the requirements files
    """
    req_dict = {}
    with open(filename, 'r') as req_file:
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
                        puts(colored.red('%s doesn\' have a version number' % requirement))

    return req_dict

def get_release_date(requirement, version=None):
    j = None
    if version:
        j = urllib2.urlopen('https://pypi.python.org/pypi/%s/%s/json' % (requirement, version))
    else:
        j = urllib2.urlopen('https://pypi.python.org/pypi/%s/json' % (requirement))
    j = json.load(j)
    d = j['urls'][0]['upload_time']
    return datetime.fromtimestamp(time.mktime(time.strptime(d, '%Y-%m-%dT%H:%M:%S')))



if __name__ == '__main__':
    # use the first file as our requirements file
    req_file = None
    try:
        req_file = args.files[0]
    except:
        puts(colored.red('You need to supply at least one filename'))

    verbose = False
    if '-v' in args.all:
        verbose = True
        print "Verbose Mode!"

    if req_file:
        requirements = load_requirements(req_file)
        total_time_delta = 0
        for req, version in requirements.items():
            latest_version = get_release_date(req)
            specified_version = get_release_date(req, version)

            time_delta = (latest_version - specified_version).days
            total_time_delta = total_time_delta + time_delta

            if verbose:
                if time_delta > 0:
                    puts(colored.orange('%s (%s) is %s days out of date' % (req, version, time_delta)))
                else:
                    puts(colored.green('%s (%s) is up to date' % (req, version)))
        print "Overall, you're %s days out of date." % total_time_delta