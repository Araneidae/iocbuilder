import os.path

from iocbuilder import Device


# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['Asyn', 'AsynSerial']


class Asyn(Device):
    LibFileList = ['asyn']
    DbdFileList = ['asyn']

    

class AsynSerial(Device):
    Dependencies = (Asyn,)
    DbdFileList = ['drvAsynSerialPort']

    def __init__(self, port, name=None):
        self.__super.__init__()

        self.port = port
        self.__port_name = port.DeviceName()
        if name is None:
            name = self.__port_name[1:].replace('/', '_')
        self.__asyn_name = name

    def Initialise(self):
        print 'drvAsynSerialPortConfigure("%s", "%s", 0, 0, 0)' % (
            self.__asyn_name, self.__port_name)

    def DeviceName(self):
        return self.__asyn_name
