piprot
======

How rotten are your requirements?

![piprot Demo](http://i.imgur.com/kewPaFa.gif)

![Passing?](https://api.travis-ci.org/sesh/piprot.png)

### Installation

piprot can be installed via PyPI

    pip install piprot


### Basic Usage

Run piprot and provide a requirements file

    piprot requirements.txt

The --verbatim arguement will output your complete requirements file, with some comments about the out of date nature of your packages

    piprot --verbatim

The --verbose arguement will make things a little more verbose

    piprot --verbose requirements.txt

The --latest argument will output just the package and version number

    piprot --latest

Use the --verbatim and --latest options together to get your complete requirements file, with fully updated requirements

    piprot --verbatim --latest

Yep, you can use stdin as well

    pip freeze | piprot -


### Tests

To run the test suite, execute `python -m unittest discover`, within the project directory.

Please ensure that the (limited) tests are all passing before making a pull request. Feel free to add more.

