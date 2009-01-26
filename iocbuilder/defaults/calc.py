from iocbuilder import Device
from iocbuilder.hardware import Sscan

__all__ = ['Calc']

class Calc(Device):
    Dependencies = (Sscan,)
    LibFileList = ['calc']
    DbdFileList = ['calcSupport']
    AutoInstantiate = True
