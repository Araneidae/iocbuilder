#!/usr/bin/env python

import sys
import os
here = os.path.dirname(__file__)
sys.path.append(os.path.realpath(os.path.join(here, '../../..')))
import iocbuilder

iocbuilder.ConfigureIOC(architecture = 'linux-x86')

iocbuilder.IocCommand('epicsEnvShow TOP')

iocbuilder.WriteNamedIoc(
    os.path.join(here, '..'), 'TS-TEST-IOC-01',
    keep_files = ['Makefile', 'etc', 'README', '.svn'],
    makefile_name = 'Makefile.builder')
