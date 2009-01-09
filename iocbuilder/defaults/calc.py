from iocbuilder import Device
from iocbuilder.hardware import Sscan

__all__ = ['Transform']

class Transform(Device):
    '''Implementation of transform record type.'''
    Dependencies = (Sscan,)
    LibFileList = ['calc']
    DbdFileList = ['calcSupport']
