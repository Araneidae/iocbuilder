import os.path

from iocbuilder import Device
from iocbuilder.support import quote_c_string
from iocbuilder.validators import strOrNone, intOrNone

# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['Asyn', 'AsynSerial']


class Asyn(Device):
    LibFileList = ['asyn']
    DbdFileList = ['asyn']
    AutoInstantiate = True
    

class AsynSerial(Device):
    Dependencies = (Asyn,)
    DbdFileList = ['drvAsynSerialPort']

    # Set of allocated ports to avoid accidential duplication.
    __Ports = set()

    # Flag used to identify this as an asyn device.
    IsAsyn = True

    ArgInfo = [
        ('port', None, 'Serial port'),
        ('name', strOrNone, 'Override name', None),
        ('input_eos', strOrNone, 'Input end of string (terminator)', None),
        ('output_eos', strOrNone, 'Output end of string (terminator)', None),
        ('baud', int, 'Baud Rate'),
        ('bits', int, 'Bits'),
        ('parity', str, 'Parity'),
        ('stop', int, 'Stop Bits'),
        ('clocal', None, 'clocal?'), 
        ('crtscts', None, 'crtscts?')
    ]
    XMLObjects = ['port']
    def __init__(self, port, name, input_eos, output_eos, **options):
        self.__super.__init__()

        self.port = port
        self.port_name = port.DeviceName()
        
        if name is None:
            name = self.port_name[1:].replace('/', '_')
        assert name not in self.__Ports, \
            'AsynSerial port %s already defined' % name
        self.__Ports.add(name)
        self.asyn_name = name

        self.options = options
        self.input_eos = input_eos
        self.output_eos = output_eos
        
    def Initialise(self):
        print 'drvAsynSerialPortConfigure("%s", "%s", 0, 0, 0)' % (
            self.asyn_name, self.port_name)
        for key, value in self.options:
            print 'asynSetOption("%s", 0, "%s", "%s")' % (
                self.asyn_name, key, value)
        if self.input_eos is not None:
            print 'asynOctetSetInputEos("%s", 0, %s)' % (
                self.asyn_name, quote_c_string(self.input_eos))
        if self.output_eos is not None:
            print 'asynOctetSetOutputEos("%s", 0, %s)' % (
                self.asyn_name, quote_c_string(self.output_eos))

    def DeviceName(self):
        return self.asyn_name

    def __str__(self):
        return self.asyn_name
