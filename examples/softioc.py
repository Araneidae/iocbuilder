#!/usr/bin/env python

import sys
import os
sys.path.append(
    os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
import iocbuilder

iocbuilder.ConfigureIOC(architecture = 'linux-x86')

iocbuilder.IocCommand('epicsEnvShow TOP')

iocbuilder.WriteIoc('iocs', 'TS', 'SOFT', 1)
