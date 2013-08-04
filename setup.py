#!/usr/bin/env python
from setuptools import setup
import re
import sys


setup(
    name="funconf",
    version='0.0.0',
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
    install_requires=['pyyaml', 'funcsigs'],
)

