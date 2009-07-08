# ----------------------------------------------------------------------
#   Generic library support: iocBase, ipacLib and others

import os.path

from iocbuilder import Device, Architecture
from iocbuilder.configure import Call_TargetOS
from iocbuilder.iocinit import iocInit


class epicsBase(Device):
    DbdFileList = ['base']

    # This *must* initialise before anything else!
    InitialisationPhase = Device.FIRST

    def SetIocName(self, ioc_name):
        self.ioc_name = ioc_name

        
    def InitialiseOnce_vxWorks(self):
        print 'ld < bin/%s/%s.munch' % (Architecture(), self.ioc_name)

    def InitialiseOnce(self):
        iocInit.cd_home()
        Call_TargetOS(self, 'InitialiseOnce')
        print 'dbLoadDatabase "dbd/%s.dbd"' % self.ioc_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            self.ioc_name.replace('-', '_')


def EpicsBasePath():
    return epicsBase.LibPath()
