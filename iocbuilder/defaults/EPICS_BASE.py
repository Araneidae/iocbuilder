# ----------------------------------------------------------------------
#   Generic library support: iocBase, ipacLib and others

import os.path

from iocbuilder import Device


class epicsBase(Device):
    DbdFileList = ['base']

    # This *must* initialise before anything else!
    InitialisationPhase = Device.FIRST

    def SetIocName(self, ioc_name):
        self.ioc_name = ioc_name

    def InitialiseOnce(self):
        dbd_name = self.ioc_name
        print 'cd homeDir'
        print 'ld < bin/%s/%s.munch' % (self.Arch(), self.ioc_name)
        print 'dbLoadDatabase "dbd/%s"' % dbd_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            dbd_name.replace('-', '_')


def EpicsBasePath():
    return epicsBase.LibPath()
