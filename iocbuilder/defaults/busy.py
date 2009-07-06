from iocbuilder import Device

__all__ = ['Busy']

class Busy(Device):
    LibFileList = ['busy']
    DbdFileList = ['busySupport']
    AutoInstantiate = True
