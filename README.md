piprot
======

How rotten are your requirements?

![piprot Demo](http://i.imgur.com/kewPaFa.gif)

### Installation

piprot can now be installed

    python setup.py install


### Basic Usage

Just a heads up that this readme doesn't even scratch the surface of what's possible with this initial version of piprot.

piprot will always use the first requirements file you include on the comand line

    piprot requirements.txt

The --verbose arguement will make things a little more verbose

    piprot --verbose requirements.txt

The --verbatim arguement will output your complete requirements file, with some comments about the out of date nature of your packages

    piprot --verbatim

The --latest argument will output just the package and version number

    piprot --latest

Use the --verbatim and --latest options together to get your complete requirements file, with fully updated requirements

    piprot --verbatim --latest

Yep, you can use stdin as well

    pip freeze | piprot -


### Tests

To run the test suite, execute `python -m unittest discover`, within the project directory.

Test coverage is pretty low at the moment.
