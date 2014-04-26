#!/usr/bin/env python
from setuptools import setup
import re
import sys


requires = ["pyyaml"]
VERSION = sys.version_info[:2] 
if VERSION < (3, 3):
    requires.append('funcsigs')
if VERSION == (2, 6):
    requires.append('ordereddict')

PYTHON3K = sys.version_info[0] > 2
setup(
    name="funconf",
    version='0.2.5',
    py_modules=['funconf'],
    author="Michael Dorman",
    author_email="mjdorma@gmail.com",
    url="https://github.com/mjdorma/funconf",
    description="Function Configuration",
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
    tests_require=["mock"] + [] if PYTHON3K else ['unittest2'],
    test_suite="tests" if PYTHON3K else "unittest2.collector", 
    install_requires=requires,
)

