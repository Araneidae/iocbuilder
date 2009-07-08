#!/usr/bin/env python2.4

import os
import sys


# Boilerplate required at start of build script.  Need to run Configure()
# before importing the builder!

# from pkg_resources import require
# require('dls.builder')
sys.path.append('/home/mga83/epics/iocbuilder')

import iocbuilder
iocbuilder.ConfigureIOC()
from iocbuilder import *

# Specify versions of components to be used.
ModuleVersion('ipac',       '2-8dls4-3')
ModuleVersion('Hy8401ip',   '3-11')


# Create some hardware resources
card9 = hardware.Hy8002(9)
adc = card9.Hy8401(0)  # Slot A


# Specify creating records for TS-XX-DEV-01
SetDomain('TS', 'XX')
SetDevice('DEV', 1)

for i in range(8):
    adc.channel(i).ai('AI%d' % (i+1), EGU = 'V', PREC = 4)


# Write IOC to $(pwd)/TS/XX
SetTargetDir(None)
WriteIoc(os.getcwd(), 'TS', 'XX', 1)
