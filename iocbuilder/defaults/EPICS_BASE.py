# EPICS_BASE ensures base.dbd is loaded.  Everything else is currently done
# in iocinit.

from iocbuilder import Device, IocCommand, ModuleBase, EpicsEnvSet
from iocbuilder import configure
from iocbuilder.arginfo import *

class epicsBase(Device):
    DbdFileList = ['base']

    InitialisationPhase = Device.FIRST

    def __init__(self, ioc_init):
        self.__super.__init__()
        self.ioc_init = ioc_init

    def Initialise_vxWorks(self):
        print 'ld < bin/%s/%s.munch' % (
            configure.Architecture(), self.ioc_init.ioc_name)

    def Initialise_FIRST(self):
        self.ioc_init.cd_home()
        configure.Call_TargetOS(self, 'Initialise')
        print
        print 'dbLoadDatabase "dbd/%s.dbd"' % self.ioc_init.ioc_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            self.ioc_init.ioc_name.replace('-', '_')


class StartupCommand(ModuleBase):
    '''Add some text to the startup script'''
    def __init__(self, command, post_init=False):
        IocCommand(command, post_init)
        self.__super.__init__()

    ArgInfo = makeArgInfo(__init__,
        command   = Simple('Startup command', str),
        post_init = Simple('If True, do this after iocInit', bool))

class EpicsEnvSet(ModuleBase):
    '''Set a variable in the EPICS environment'''
    _EpicsEnvSet = EpicsEnvSet
    def __init__(self, key, value):
        self._EpicsEnvSet(key, value)
        self.__super.__init__()

    ArgInfo = makeArgInfo(__init__,
        key   = Simple('Variable to set', str),
        value = Simple('Value to set it to', str))
