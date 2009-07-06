from iocbuilder import Device

__all__ = ['Std']

class Std(Device):
    LibFileList = ['std']
    DbdFileList = ['stdSupport']
    AutoInstantiate = True
