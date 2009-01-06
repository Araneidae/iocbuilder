#!/bin/env python2.4
# green of a setup.py file for any dls module
from setuptools import setup, find_packages, Extension

# this line allows the version to be specified in the release script
try:
    version = version
except:
    version = "development"

setup(
#     # install_requires allows you to import a specific version of a module in
#     # your scripts, setup_requires lets us use the site specific settings for
#     # installing scripts
#     setup_requires = ["dls.environment==1.0"],
#     # name of the module
#     name = "iocbuilder",
#     # version: over-ridden by the release script
#     version = version,
#     packages = [
#         "dls", "dls.builder",
#         "dls.builder.hardware", "dls.builder.modules", "dls.builder.defaults"],
#     package_dir = {
#         'dls': 'dls',
#         'dls.builder': 'src'},
# #        'dls.builder.hardware': 'src/hardware'},
#     namespace_packages = ['dls'],
    name = 'iocbuilder',
    version = version,
    description = 'IOC builder',
    author = 'Michael Abbott',
    author_email = 'Michael.Abbott@diamond.ac.uk',
    
    include_package_data = True,
    zip_safe = False
    )
