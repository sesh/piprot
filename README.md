piprot
======

How rotten are your requirements?

![piprot Demo](http://i.imgur.com/kewPaFa.gif)


### Installation

piprot can be installed via PyPI

    pip install piprot


### Basic Usage

Run piprot and provide a requirements file (if it's not called requirements.txt)

    piprot base_requirements.txt


The --verbatim arguement will output your complete requirements file, with some comments about the out of date nature of your packages.

    piprot --verbatim

Using --outdated will show only the out of date requirements, pretty much the same as running `pip list -o`, except on a requirements file.

    piprot --outdated

Yep, you can use stdin as well

    pip freeze | piprot


### Tests

To run the test suite, execute `python -m unittest discover`, within the project directory.

Please ensure that the (limited) tests are all passing before making a pull request. Feel free to add more.

