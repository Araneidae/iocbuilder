from iocbuilder import Substitution, Device

__all__ = ['IOCinfo']

class IOCinfo(Substitution, Device):
    '''Provides basic information about the IOC, supplementing the information
    provided by vxStats: provides temperature information.'''
    # __init__ arguments
    ArgInfo = [('device', str, 'Device Prefix')]
    # Substitution attributes
    TemplateFile = 'IOCinfo.template'
    # Device attributes    
    DbdFileList = ['IOCinfo']
    LibFileList = ['IOCinfo']
