from iocbuilder import Device

__all__ = ['Sscan']

class Sscan(Device):
    ModuleName = 'sscan'

    LibFileList = ['sscan']
    DbdFileList = ['sscanSupport.dbd']
