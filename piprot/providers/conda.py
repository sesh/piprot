# Based on https://github.com/conda/conda-api
# only package_info call is kept

import json
from subprocess import Popen, PIPE
from os.path import join
import sys


def _call_conda(extra_args, basepath=None):
    # call conda with the list of extra arguments, and return the tuple
    # stdout, stderr
    if basepath:
        if sys.platform == 'win32':
            python = join(basepath, 'python.exe')
            conda = join(basepath, 'Scripts', 'conda-script.py')
        else:
            python = join(basepath, 'bin/python')
            conda = join(basepath, 'bin/conda')

        cmd_list = [python, conda]
    else:  # just use whatever conda is on the path
        cmd_list = ['conda']

    cmd_list.extend(extra_args)
    try:
        p = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
    except OSError:
        raise Exception("could not invoke %r\n" % cmd_list)
    return p.communicate()


def _call_and_parse(extra_args, basepath=None):
    stdout, stderr = _call_conda(extra_args, basepath=basepath)
    if stderr.decode().strip():
        raise Exception('conda %r:\nSTDERR:\n%s\nEND' % (extra_args,
                                                         stderr.decode()))
    return json.loads(stdout.decode())


def package_info(package, basepath=None):
    """
    Return a dictionary with package information.
    """
    return _call_and_parse(['info', package, '--json'], basepath=basepath)
