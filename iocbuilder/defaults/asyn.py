import os.path

from iocbuilder import Device, makeArgInfo
from iocbuilder.support import quote_c_string


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

    ValidSetOptionKeys = set([
        'baud', 'bits', 'parity', 'stop', 'clocal', 'crtscts'])

    def __init__(self, port,
            name=None, input_eos=None, output_eos=None,
            priority=100, noAutoConnect=0, noProcessEos=0, **options):
        self.__super.__init__()

        self.port = port
        self.port_name = port.DeviceName()
        
        if name is None:
            name = self.port_name[1:].replace('/', '_')
        assert name not in self.__Ports, \
            'AsynSerial port %s already defined' % name
        self.__Ports.add(name)
        self.asyn_name = name

        assert set(options.keys()) <= self.ValidSetOptionKeys, \
            'Invalid argument to asynSetOption'
        self.options = options
        self.input_eos = input_eos
        self.output_eos = output_eos
        self.priority = priority
        self.noAutoConnect = noAutoConnect
        self.noProcessEos = noProcessEos
        
    ArgInfo = makeArgInfo(__init__,
        port          = (Device, 'Serial port'),
        name          = (str, 'Override name'),
        input_eos     = (str, 'Input end of string (terminator)'),
        output_eos    = (str, 'Output end of string (terminator)'),
        priority      = (int, "Priority"),
        noAutoConnect = (int, "Set to 1 to stop autoconnect"),
        noProcessEos  = (int, "Set to 1 to avoid processing end of string"),
        # SetOption keys
        baud    = (int, 'Baud Rate'),
        bits    = (int, 'Bits'),
        parity  = (str, 'Parity'),
        stop    = (int, 'Stop Bits'),
        clocal  = (None, 'clocal?'), 
        crtscts = (None, 'crtscts?'))
        
        
    def Initialise(self):
        print 'drvAsynSerialPortConfigure(' \
            '"%(asyn_name)s", "%(port_name)s", ' \
            '%(priority)d, %(noAutoConnect)d, %(noProcessEos)d)' % \
                self.__dict__
        for key, value in self.options.items():
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
