piprot
======

How rotten are your requirements?

![piprot Screenshot](http://i.imgur.com/JR9yCul.png)

### Basic Usage

Just a heads up that this readme doesn't even scratch the surface of what's possible with this initial version of piprot.

piprot will always use the first requirements file you include on the comand line

    ./piprot.py requirements.txt

The -v arguement will make things a little more verbose

    ./piprot.py -v requirements.txt

The -l or --lint will get angry at you about mistakes in your requirements file

    ./piprot.py --lint requirements.txt

Yes, you can use stdin as well

    pip freeze | ./piprot.py

### Tests

To run the test suite, execute `python -m unittest discover`, within the project directory.
