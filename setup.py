from setuptools import setup

# these lines allow the version to be specified in Makefile.private
import os
version = os.environ.get("MODULEVER", "development")

setup(
    name = 'iocbuilder',
    version = version,
    description = 'IOC builder',
    author = 'Michael Abbott',
    author_email = 'Michael.Abbott@diamond.ac.uk',
    install_requires = ['dls_dependency_tree==2.1', 'dls_edm==1.29'],
    packages = ['iocbuilder', 'xmlbuilder'],
    package_data = { 'iocbuilder': ['defaults/*.py', 'defaults/*/*.py'],
                     'xmlbuilder': ['xeb.png'] },
    entry_points = {
        'console_scripts':
            ['xeb = xmlbuilder.xeb:main',
             'dls-xml-iocbuilder.py = xmlbuilder.xmlbuilder:main']},
    zip_safe = False)
