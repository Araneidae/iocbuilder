from iocbuilder import Device

__all__ = ['Sscan']

class Sscan(Device):
    LibFileList = ['sscan']
    DbdFileList = ['sscanSupport']
    AutoInstantiate = True
