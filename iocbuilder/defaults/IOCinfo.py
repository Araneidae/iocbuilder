from iocbuilder import Substitution, Device, makeArgInfo

__all__ = ['IOCinfo']

class IOCinfo(Substitution, Device):
    '''Provides basic information about the IOC, supplementing the information
    provided by vxStats: provides temperature information.'''

    Arguments = ('device',)
    # Substitution attributes
    TemplateFile = 'IOCinfo.template'
    # Device attributes    
    DbdFileList = ['IOCinfo']
    LibFileList = ['IOCinfo']

    def __init__(self, iocname):
        self.__super.__init__(device = iocname)
    ArgInfo = makeArgInfo(__init__, iocname = (str, 'Device Prefix'))
