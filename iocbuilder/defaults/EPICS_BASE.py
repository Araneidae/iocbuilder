# EPICS_BASE ensures base.dbd is loaded.  Everything else is currently done
# in iocinit.

from iocbuilder import Device, IocCommand, ModuleBase, EpicsEnvSet, PreBootCommandSet
from iocbuilder import configure
from iocbuilder.support import quote_c_string
from iocbuilder.arginfo import *

class epicsBase(Device):
    DbdFileList = ['base']

    InitialisationPhase = Device.FIRST

    def __init__(self, ioc_init):
        self.__super.__init__()
        self.ioc_init = ioc_init

    def Initialise_vxWorks(self):
        print 'ld < bin/%s/%s.munch' % (
            configure.Architecture(), self.ioc_init.ioc_name)

    def Initialise_FIRST(self):
        self.ioc_init.cd_home()
        configure.Call_TargetOS(self, 'Initialise')
        print
        print 'dbLoadDatabase "dbd/%s.dbd"' % self.ioc_init.ioc_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            self.ioc_init.ioc_name.replace('-', '_')


class StartupCommand(Device):
    '''Add some text to the startup script'''
    def __init__(self, command, post_init=False, at_end = True):
        self.__super.__init__()
        if at_end:
            # Backwards compatible behaviour, goes at end of startup commands
            IocCommand(command, post_init)
        else:
            self.command = command
            if post_init:
                self.PostIocInitialise = self.__print_command
            else:
                self.Initialise = self.__print_command

    def __print_command(self):
        print self.command

    ArgInfo = makeArgInfo(__init__,
        command   = Simple('Startup command', str),
        post_init = Simple('If True, do this after iocInit', bool),
        at_end    = Simple('If not set command generated in sequence', bool))


@defArgInfo(
    pv    = Simple('PV name'),
    value = Simple('Value to put to PV'))
def dbpf(pv, value):
    """Set a pv to a value after iocInit in the startup script"""
    StartupCommand('dbpf "%s", "%s"' % (pv, value), post_init=True, at_end=False)


class EpicsEnvSet(ModuleBase):
    '''Set a variable in the EPICS environment'''
    _EpicsEnvSet = EpicsEnvSet
    def __init__(self, key, value):
        self._EpicsEnvSet(key, value)
        self.__super.__init__()

    ArgInfo = makeArgInfo(__init__,
        key   = Simple('Variable to set', str),
        value = Simple('Value to set it to', str))


class PreBootCommandSet(ModuleBase):
    '''Set commands to run before IOC startup'''
    _PreBootCommandSet = PreBootCommandSet
    def __init__(self, command):
        self._PreBootCommandSet(command)
        self.__super.__init__()

    ArgInfo = makeArgInfo(__init__,
        command = Simple('Command to run before IOC startup', str))


def dotted_to_ip(dotted):
    quads = map(int, dotted.split('.'))
    assert len(quads) == 4, 'Ip address must have four numbers'
    assert min(quads) >= 0 and max(quads) < 256, 'Invalid numeric range'
    return quads[3] | (quads[2] << 8) | (quads[1] << 16) | (quads[0] << 24)


class IpAttach(Device):
    '''Enables secondary network attached to secondary network port on MVME5500
    card.'''

    def __init__(self, address,
            mask = '255.255.255.0', device = 'wancom', port = 0):
        self.__super.__init__()
        dotted_to_ip(address)       # Just validate address
        self.address = address
        self.mask = dotted_to_ip(mask)
        self.device = device
        self.port = port

    def Initialise(self):
        print 'ipAttach(%(port)d, "%(device)s")' % self.__dict__
        print 'ifMaskSet("%(device)s%(port)d", 0x%(mask)08x)' % self.__dict__
        print 'ifAddrSet("%(device)s%(port)d", "%(address)s")' % self.__dict__

    ArgInfo = makeArgInfo(__init__,
        address = Simple('IP address to bind to secondary network'),
        mask = Simple('Netmask for network bound to secondary port'),
        device = Simple('Internal device name of secondary network port'),
        port = Simple('Port number of secondary network port', int))


class hostAdd(Device):
    """Bind a host name to an IP address on vxWorks"""
    def __init__(self, host, address):
        self.__super.__init__()
        dotted_to_ip(address)
        self.host = host
        self.address = address

    def Initialise(self):
        print 'hostAdd("%(host)s", "%(address)s")' % self.__dict__

    ArgInfo = makeArgInfo(__init__,
        host = Simple("Host name to be bound to given address"),
        address = Simple("IP address to bind to given host name"))
        
class system(Device):
    """
    A generic class to execute commands from an IOC startup script. Wraps the 
    system() call, so any precautions there apply here as well. Special 
    characters will be escaped.
    """
    DbdFileList = ['system']

    def __init__(self, command):
        self.__super.__init__()
        self.command = command

    def PostIocInitialise(self):
        print 'system %s' % quote_c_string(self.command)
        
    ArgInfo = makeArgInfo(__init__,
        command = Simple("Command to be run post IOC init"))

