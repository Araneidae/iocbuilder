# ----------------------------------------------------------------------
#   Generic library support: iocBase, ipacLib and others

import os.path

from device import Device


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
