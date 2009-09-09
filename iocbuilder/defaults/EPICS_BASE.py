# EPICS_BASE ensures base.dbd is loaded.  Everything else is currently done
# in iocinit.

from iocbuilder import Device, IocCommand, ModuleBase
from iocbuilder.arginfo import *

class epicsBase(Device):
    DbdFileList = ['base']

class StartupCommand(ModuleBase):
    def __init__(self, command, post_init=False):
        IocCommand(command, post_init)
        self.__super.__init__()
        
    ArgInfo = makeArgInfo(__init__,
        command   = Simple('Startup command', str),
        post_init = Simple('If True, do this after iocInit', bool))
