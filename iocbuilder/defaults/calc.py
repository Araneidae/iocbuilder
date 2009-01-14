from iocbuilder import Device
from iocbuilder.hardware import Sscan

__all__ = ['Calc']

class Calc(Device):
    '''Implementation of transform record type.'''
    Dependencies = (Sscan,)
    LibFileList = ['calc']
    DbdFileList = ['calcSupport']
