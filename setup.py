#!/usr/bin/env python
from setuptools import setup
import re
import sys


def load_version(filename='begin_fu/version.py'):
    "Parse a __version__ number from a source file"
    with open(filename) as source:
        text = source.read()
        match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", text)
        if not match:
            msg = "Unable to find version number in {}".format(filename)
            raise RuntimeError(msg)
        version = match.group(1)
        return version


setup(
    name="begins_fu",
    version=load_version(),
    packages=['begin_fu'],
    zip_safe=False,
    author="Michael Dorman",
    author_email="mjdorma@gmail.com",
    description="Fun with begins",
    long_description=open('README.rst').read(),
    license="ASL",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': [
            'shutil = begin_fu.wrap_shutil:main.start'
            ]
    },
    install_requires=['begins', 'pyyaml'],
)
