piprot
======

How rotten are your requirements?

![piprot Screenshot](http://i.imgur.com/JR9yCul.png)

### Installation

piprot can now be installed

    python setup.py install


### Basic Usage

Just a heads up that this readme doesn't even scratch the surface of what's possible with this initial version of piprot.

piprot will always use the first requirements file you include on the comand line

    piprot requirements.txt

The -v arguement will make things a little more verbose

    piprot -v requirements.txt

The -l or --lint will get angry at you about mistakes in your requirements file

    piprot --lint requirements.txt

Yes, you can use stdin as well

    pip freeze | piprot -


### Tests

To run the test suite, execute `python -m unittest discover`, within the project directory.

Test coverage is pretty low at the moment.
