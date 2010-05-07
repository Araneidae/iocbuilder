#!/bin/env dls-python2.4

# setup the path
from pkg_resources import require
require("dls_dependency_tree")
require("iocbuilder")

# import modules
import iocbuilder
from dls_dependency_tree import dependency_tree

# parse the options supplied to the program
options, args = iocbuilder.ParseEtcArgs(architecture="linux-x86")
iocbuilder.ParseAndConfigure(options, dependency_tree)

# import the builder objects
from iocbuilder.modules import *

# make some objects
if options.debug:
    print "Creating builder objects..."
eurothermSim = pyDrv.serial_sim_instance(
    name='eurothermSim', pyCls='eurotherm2k', module='eurotherm2k_sim',
    IPPort=8100, rpc=9001)
asyn.AsynIP(
    name='eurothermAsyn', port='172.23.111.180:7001', simulation=eurothermSim)
eurotherm2k.eurotherm2k(
    P='EUROTHERM2K', Q='', PORT='eurothermAsyn', GAD=0, LAD=1)
if options.debug:
    print "Done"

# write the IOC
iocbuilder.WriteNamedIoc(options.iocpath, options.iocname, substitute_boot=True)
