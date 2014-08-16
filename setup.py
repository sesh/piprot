from setuptools import setup

"""
Use pandoc to convert README.md to README.rst before uploading
   pandoc README.md -o README.rst
"""

setup(
    name='piprot',
    version='0.7.2',
    author='Brenton Cleeland, Mark Hellewell, Dan Peade',
    author_email='brenton@brntn.me',
    packages=['piprot',],
    url='http://github.com/sesh/piprot',
    license='LICENSE.txt',
    description='How rotten are your requirements?',
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'piprot = piprot.piprot:piprot',
        ]
    },
    install_requires=[
        'requests',
        'six'
    ]
)
