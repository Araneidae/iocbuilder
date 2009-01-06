from iocbuilder import Substitution, Device

__all__ = ['IOCinfo']

class IOCinfo(Substitution, Device):
    '''Provides basic information about the IOC, supplementing the information
    provided by vxStats: provides temperature information.'''
    
    Arguments = ('device',)
    TemplateFile = 'IOCinfo.template'
    
    DbdFileList = ['IOCinfo.dbd']
    LibFileList = ['IOCinfo']

    def __init__(self, iocname):
        '''Creates an IOCinfo expansion instance for the named ioc.'''
        self.__super.__init__(device = iocname)
