import os.path

from iocbuilder import Device, SetSimulation, DummySimulation
from iocbuilder.support import quote_c_string
from iocbuilder.arginfo import *

try:
    from iocbuilder.modules.pyDrv import serial_sim
except:
    serial_sim = Device

# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['Asyn', 'AsynSerial', 'AsynIP']


class Asyn(Device):
    LibFileList = ['asyn']
    DbdFileList = ['asyn']
    AutoInstantiate = True
    

class AsynPort(Device):
    Dependencies = (Asyn,)

    # Set of allocated ports to avoid accidential duplication.
    __Ports = set()

    # Flag used to identify this as an asyn device.
    IsAsyn = True

    def __init__(self, name):
        self.asyn_name = name
        assert name not in self.__Ports, \
            'AsynPort %s already defined' % name
        self.__Ports.add(name)
        self.__super.__init__()
                
    def DeviceName(self):
        return self.asyn_name

    def __str__(self):
        return self.DeviceName()


class AsynOctetInterface(AsynPort):

    ValidSetOptionKeys = set([
        'baud', 'bits', 'parity', 'stop', 'clocal', 'crtscts'])

    def __init__(self, port,
            name=None, input_eos=None, output_eos=None,
            priority=100, noAutoConnect=False, noProcessEos=False,
            simulation=None, **options):
        self.port_name = port
        assert set(options.keys()) <= self.ValidSetOptionKeys, \
            'Invalid argument to asynSetOption'
        self.options = options
        self.input_eos = input_eos
        self.output_eos = output_eos
        self.priority = priority
        self.noAutoConnect = int(noAutoConnect)
        self.noProcessEos = int(noProcessEos)
        self.__super.__init__(name)    
               
    def Initialise(self):
        print '%sConfigure("%s", "%s", %d, %d, %d)' % (
            self.DbdFileList[0], self.asyn_name, self.port_name, self.priority,
            self.noAutoConnect, self.noProcessEos)    
        for key, value in self.options.items():
            print 'asynSetOption("%s", 0, "%s", "%s")' % (
                self.asyn_name, key, value)
        if self.input_eos is not None:
            print 'asynOctetSetInputEos("%s", 0, %s)' % (
                self.asyn_name, quote_c_string(self.input_eos))
        if self.output_eos is not None:
            print 'asynOctetSetOutputEos("%s", 0, %s)' % (
                self.asyn_name, quote_c_string(self.output_eos))
                                
    _common_args = dict(
        name          = Simple('Override name', str),
        input_eos     = Simple('Input end of string (terminator)', str),
        output_eos    = Simple('Output end of string (terminator)', str),
        priority      = Simple('Priority', int),
        noAutoConnect = Simple('Set to stop autoconnect', bool),
        noProcessEos  = Simple('Set to avoid processing end of string', bool),
        simulation    = Ident ('serial_sim object to use as a simulation', serial_sim),        
        # SetOption keys        
        baud          = Simple('Baud Rate', int),
        bits          = Simple('Bits', int),
        parity        = Simple('Parity', str),
        stop          = Simple('Stop Bits', int),
        clocal        = Simple('clocal?', int),
        crtscts       = Simple('crtscts?', int))


class AsynSerial(AsynOctetInterface):
    '''Asyn Serial Port'''

    DbdFileList = ['drvAsynSerialPort']

    # just get the port_name from the serial port, and pass it up
    def __init__(self, port, name = None, **kwargs):
        self.port = port
        port_name = port.DeviceName()
        if name is None:
            name = port_name[1:].replace('/', '_')
        self.__super.__init__(port_name, name, **kwargs)
        
    # __init__ attributes
    ArgInfo = makeArgInfo(AsynOctetInterface.__init__,
        AsynOctetInterface.ValidSetOptionKeys,
        port = Ident('Serial port', Device), 
        **AsynOctetInterface._common_args)

class dummyAsyn(DummySimulation):  
    def DeviceName(self):
        return "dummyAsynPort"
    def __str__(self):
        return "dummyAsynPort"

def AsynSerial_sim(port, name, simulation = None, **kwargs):
    if simulation is None:
        return dummyAsyn()
    else:
        portname = simulation.startSerial()
        class DummyPort:
            def DeviceName(self): return portname
        return AsynSerial_real(DummyPort(), name, **kwargs)
AsynSerial_real = AsynSerial
SetSimulation(AsynSerial, AsynSerial_sim)                        

class AsynIP(AsynOctetInterface):
    '''Asyn IP Port'''

    DbdFileList = ['drvAsynIPPort']  
    
    # validate the port then pass it up
    def __init__(self, port, name = None, **kwargs):
        IsIpAddr(port)
        if name is None:
            name = port.replace(".", "_").replace(":","_")
        self.__super.__init__(port, name, **kwargs)       
        
    # __init__ attributes
    ArgInfo = makeArgInfo(AsynOctetInterface.__init__,
        AsynOctetInterface.ValidSetOptionKeys,
        port = Simple('IP address', str), 
        **AsynOctetInterface._common_args)    

def AsynIP_sim(port, name, simulation = None, **kwargs):
    if simulation is None:
        return dummyAsyn()
    else:
        port = simulation.startIP()
        return AsynIP_real(port, name, **kwargs)
AsynIP_real = AsynIP

SetSimulation(AsynIP, AsynIP_sim)      

def IsIpAddr(val):
    # validator for an ip address
    errStr = "Should be of format x[xx].x[xx].x[xx].x[xx][:x[x..]]"
    # split into ip and port
    split = val.strip().split(":")
    # check we have either just an ip, or an ip and a port
    assert len(split)in [1,2], errStr
    # check the port is in an int if it exists
    if len(split) == 2:
        assert split[1].isdigit(), errStr
    if split[0] == "localhost":
        return
    # split the ip by .
    split = split[0].split(".")
    # check there are 4 elements
    assert len(split) == 4, errStr
    # and that each element is an integer in the range 0..255
    for i in split:
        assert i.isdigit() and int(i) in range(256), errStr
