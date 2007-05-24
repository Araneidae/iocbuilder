import os.path

from _epics import Device


# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['AsynSerial']


class Asyn(Device):
    ModuleName = 'asyn'

    LibFileList = ['asyn']
    DbdFileList = ['asyn.dbd']

    

class AsynSerial(Device):
    ModuleName = Asyn.ModuleName
    Dependencies = (Asyn,)

    DbdFileList = ['drvAsynSerialPort.dbd']

    def __init__(self, port, name=None):
        self.__super.__init__()
        
        self.raw_port = port.DeviceName()
        if name is None:
            name = self.raw_port[1:].replace('/', '_')
        self.name = name

    def Initialise(self):
        print 'drvAsynSerialPortConfigure("%s", "%s", 0, 0, 0)' % (
            self.name, self.raw_port)

    def DeviceName(self):
        return self.name
