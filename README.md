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

Yes, you can use stdin as well

    pip freeze | ./piprot.py