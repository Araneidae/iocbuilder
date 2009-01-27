#!/bin/env python2.4
# green of a setup.py file for any dls module
from setuptools import setup, find_packages, Extension

# this line allows the version to be specified in the release script
try:
    version = version
except:
    version = "development"

setup(
    name = 'iocbuilder',
    version = version,
    description = 'IOC builder',
    author = 'Michael Abbott',
    author_email = 'Michael.Abbott@diamond.ac.uk',
    packages = ['iocbuilder'],
    package_data = { 'iocbuilder': ['defaults/*.py'] },
    zip_safe = False)
