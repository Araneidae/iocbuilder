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
    install_requires = ['dls_dependency_tree', 'dls_edm'],
    packages = ['iocbuilder', 'xmlbuilder', 'toolkit'],
    package_data = { 'iocbuilder': ['defaults/*.py', 'defaults/*/*.py'],
                     'xmlbuilder': ['xeb.png'] },
    entry_points = {
        'console_scripts':
            ['xeb = xmlbuilder.xeb:main',
             'dls-xml-iocbuilder.py = xmlbuilder.xmlbuilder:main', 
             'dls-print-template-macros.py = toolkit.print_template_macros:print_template_macros']},
    zip_safe = False)
