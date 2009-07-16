# EPICS_BASE ensures base.dbd is loaded.  Everything else is currently done
# in iocinit.

from iocbuilder import Device

class epicsBase(Device):
    DbdFileList = ['base']
