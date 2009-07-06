from iocbuilder import Device

__all__ = ['Dc1394']

class Dc1394(Device):
    LibFileList = ['dc1394']
    AutoInstantiate = True
