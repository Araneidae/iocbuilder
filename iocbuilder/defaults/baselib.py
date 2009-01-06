# ----------------------------------------------------------------------
#   Generic library support: iocBase, ipacLib and others

import os.path

from iocbuilder import *

# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['vxStats', 'mbbi32Direct', 'genSub', 'Transform', 'IOCinfo']




# The iocBase library must be loaded first before all other libraries.
# This loads the core files used to make up an EPICS IOC.
#
# We take the opportunity to generate some useful early IOC initialisation
# code at the same time.
class iocBase(Device):
    '''Core IOC library (for 3.13 and 3.14.6 only).  This library should be
    loaded before anything else is loaded.'''

    ModuleName = 'baseTop'

    LibFileList = ['iocCore', 'baseLib', 'initHooks.o']
    DbdFileList = ['baseApp.dbd']

    def SetIocName(self, ioc_name):
        pass


class epicsBase(Device):
    '''EPICS base library (for 3.14 only).  This should be loaded first.'''
    ModuleName = 'EPICS_BASE'

    DbdFileList = ['base.dbd']

    # This *must* initialise before anything else!
    InitialisationPhase = Device.FIRST

    def SetIocName(self, ioc_name):
        self.ioc_name = ioc_name

    def InitialiseOnce(self):
        dbd_name = self.ioc_name
        print 'cd homeDir'
        print 'ld < bin/%s/%s.munch' % (self.Arch(), self.ioc_name)
        print 'dbLoadDatabase "dbd/%s.dbd"' % dbd_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            dbd_name.replace('-', '_')


def EpicsBasePath():
    return epicsBase.LibPath()

        

class mbbi32Direct(Device):
    '''Implementation of mbbi32Direct record type.'''
    
    LibFileList = ['mbbi32DirectRecord.o']
    DbdFileList = ['mbbi32Direct.dbd']


class genSub(Device):
    '''Implementation of gensub record type.'''

    LibFileList = ['genSub']
    DbdFileList = ['genSubRecord.dbd']
