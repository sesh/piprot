from setuptools import setup


setup(
    name='piprot',
    version='0.7.1',
    author='Brenton Cleeland, Mark Hellewell, Dan Peade',
    author_email='brenton@brntn.me',
    packages=['piprot',],
    url='http://github.com/sesh/piprot',
    license='LICENSE.txt',
    description='How rotten are your requirements?',
    long_description=open('README.md').read(),
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
