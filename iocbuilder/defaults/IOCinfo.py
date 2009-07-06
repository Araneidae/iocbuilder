from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

class IOCinfo(Substitution, Device):
    '''Provides basic information about the IOC, supplementing the information
    provided by vxStats: provides temperature information.'''

    def __init__(self, device):
        self.__super.__init__(device = device)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        device = Simple('Device Prefix', str))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'IOCinfo.template'
    
    # Device attributes    
    DbdFileList = ['IOCinfo']
    LibFileList = ['IOCinfo']
