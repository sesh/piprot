piprot
======

How rotten are your requirements?

tl;dr: piprot allows you to check the requirements defined in your
requirements files for freshness.

.. image:: https://asciinema.org/a/2rW7dFFCKuv6g5taaUdZ70jyF.png
   :target: https://asciinema.org/a/2rW7dFFCKuv6g5taaUdZ70jyF


Installation
~~~~~~~~~~~~

The latest release of piprot can be installed via PyPI:

::

    pip install -U piprot

Basic Usage
~~~~~~~~~~~

Run piprot and provide a requirements file (if it's not called
requirements.txt) and it will tell you the current status of your
packages.

::

    > piprot base_requirements.txt
    requests (2.3.0) is up to date
    six (1.6.1) is 107 days out of date. Latest is 1.7.3
    piprot (0.6.0) is up to date
    doge (3.4.0) is 129 days out of date. Latest is 3.5.0
    Your requirements are 236 days out of date

If your requirements file is named "requirements.txt", you don't need to
provide it. piprot will automatically traverse included requirements
files.

The ``--verbatim`` argument will output your complete requirements file,
with some comments about the out of date nature of your packages.

::

    > piprot --verbatim
    # Requirements for Piprot
    # This actually doubles as a test file

    requests==2.3.0
    six==1.6.1 # Latest 1.7.3

    piprot==0.6.0
    # notarequirement==0.1.1

    doge==3.4.0 # Latest 3.5.0
    # Generated with piprot 0.7.0
    # Your requirements are 236 days out of date

Using ``--outdated`` will show only the out of date requirements, pretty
much the same as running ``pip list -o``, except on a requirements file.

::

    > piprot --outdated
    six (1.6.1) is 107 days out of date. Latest is 1.7.3
    doge (3.4.0) is 129 days out of date. Latest is 3.5.0
    Your requirements are 236 days out of date

The ``--latest`` argument will output the requirements lines with the
current version replaced with the latest version.

::

    > piprot --latest
    ipython (1.1.0) is 331 days out of date. Latest is 2.2.0
    ipython==2.2.0 # Updated from 1.1.0
    Django (1.5.4) is 241 days out of date. Latest is 1.6.5
    Django==1.6.5 # Updated from 1.5.4
    requests (1.2.3) is 356 days out of date. Latest is 2.3.0
    requests==2.3.0 # Updated from 1.2.3
    Your requirements are 928 days out of date

Personally, I like to use ``--latest`` and ``--verbatim`` together,
creating a sort-of ''perfect'' requirements file for me,

::

    > piprot --latest --verbatim
    # Development Requirements
    ipython==2.2.0 # Updated from 1.1.0

    Django==1.6.5 # Updated from 1.5.4
    requests==2.3.0 # Updated from 1.2.3
    # Generated with piprot 0.8.0
    # Your requirements are 928 days out of date

Yep, you can use stdin as well if you really want to, but there are
better tools for working with packages installed in your environment.

::

    pip freeze | piprot


(New in 0.9) You can also lookup requirements from a Github repo with the ``--github``,
``--branch`` and ``--path`` options. Additionally you can use ``--token`` to
supply a `Personal Access Token` to remotely test private repositories.

::

    > piprot -g sesh/piprot
    requests (2.4.2) is out of date. Latest is 2.4.3
    requests-futures (0.9.5) is up to date
    six (1.8.0) is up to date
    piprot (0.8.2) is up to date
    Looks like you've been keeping up to date, time for a delicious beverage!

You can also ignore packages using a norot comment in your requirements file.

::

   # Inside requirements.txt
   # Note: two spaces before # norot
   Django==1.6.5  # norot

You can set up a delay before piprot throws an error.
This is useful when you set up piprot in CI but cannot always upgrade the dependencies.

::

    > piprot --delay 7
    ipython (1.1.0) is 5 days out of date. Latest is 1.1.1
    All of your dependancies are at most 7 days out of date.
    # Displays a warning but does not throw an error


Working with your environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

piprot is designed around working with requirements defined in a
requirements file. Check out
`pip-tools <https://github.com/nvie/pip-tools>`__ if you're looking for
something similar that's designed for use against the packages that you
actually have installed.


Tests
~~~~~

To run the test suite, execute ``python -m unittest discover``, within
the project directory.

Please ensure that the (limited) tests are all passing before making a
pull request. Feel free to add more.
