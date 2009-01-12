# Generic support for IP carriers.  Only 8001 and 8002 cards exist as IP
# carriers, but a generic form of support is provided here.

import new
from iocbuilder import *

__all__ = ['IpDevice']


# All IP carriers, in particular both the 8001 and 8002, depend on the ipac
# library.  This device has no instances of its own.
class ipacLib(Device):
    '''IP carrier support library.'''
    DbdFileList = ['drvIpac']
    LibFileList = ['Ipac']


# All IpDevice instances are automatically registered and announced to all
# IpCarrier devices.  This class keeps track of all registered devices and
# ensures that each device is informed.
class _IpRegistry(Singleton):
    Carriers = []
    Devices = []
    
    def RegisterCarrier(self, carrier, name):
        self.Carriers.append(carrier)
        # Pick up any previously declared devices
        for device, name in self.Devices:
            carrier.InstallIpDevice(device, name)

    def RegisterDevice(self, device, name):
        self.Devices.append((device, name))
        # Inform all existing carriers of this new device
        for carrier in self.Carriers:
            carrier.InstallIpDevice(device, name)


# Base class for IP carrier card: both the 8001 and 8002 can act as IP
# carrier cards (though the 8001 only supports slots A and B).
class IpCarrier(Device):
    '''Support for IP carrier cards.'''
    __metaclass__ = AutoRegisterClass(
        _IpRegistry.RegisterCarrier, superclass=Device.__metaclass__)

    Dependencies = (ipacLib,)

    def __init__(self, slot, ip_support=True):
        self.__super.__init__()

        self.slot = slot
        self.IPACid = 'IPAC%d' % slot
        # Record whether this instance actually supports IP cards
        self.ip_support = ip_support
        
    @classmethod
    def InstallIpDevice(cls, device, name=None):
        '''Called internally by the global InstallIpDevice function to install
        IP support for a specific device.'''
        if not name:
            name = device.__name__
        setattr(cls, name, new.instancemethod(device, None, cls))

    def InitialiseCarrier(self, device, *args):
        '''This method should be called from the device Initialise() method
        to ensure that the carrier support is created.  If IP support was
        enabled this will ensure the driver support is initialised.'''
        if self.ip_support:
            print '%s = ipacEXTAddCarrier(&%s, "%s")' % (
                self.IPACid, device, ' '.join(map(str, args)))

    def ipmIrqCmd(self, ipslot, irq, command):
        '''This generates a call to ipmIrqCmd for the given ipslot.'''
        assert 0 <= ipslot < self.MaxIpSlots, 'Invalid IP slot: %d' % ipslot
        assert irq in [0, 1], 'Invalid irq: %s' % irq

        # Allow the command to be a string or a number in the right range.
        try:
            command = int(command)
        except ValueError:
            CommandTable = {
                'irqLevel0':    0,  'irqLevel1':    1,
                'irqLevel2':    2,  'irqLevel3':    3,
                'irqLevel4':    4,  'irqLevel5':    5,
                'irqLevel6':    6,  'irqLevel7':    7,
#                'irqGetLevel':  8,
                'irqEnable':    9,  'irqDisable':  10,
#                'irqPoll':     11,
                'irqSetEdge':  12,  'irqSetLevel': 13,
#                'irqClear':    14,
                'statUnused':  15,  'statActive':  16,
                'slotReset':   17
            }
            command = CommandTable[command]
        else:
            assert 0 <= command <= 17, 'Invalid Irq command: %d' % command

        self.AddCommand('ipmIrqCmd(%s, %d, %d, %d)' % (
            self.IPACid, ipslot, irq, command))



class IpDevice(Device):
    '''All the IP cards installed in a carrier card should be declared as
    sub-classes of this class.  They will then be automatically available as
    device factories on each defined IP carrier device.'''
    
    __metaclass__ = AutoRegisterClass(
        _IpRegistry.RegisterDevice, superclass=Device.__metaclass__)
        
    Dependencies = (ipacLib,)

    @classmethod
    def Clone(cls, newName):
        '''Clones a copy of this IP device under a new name.'''
        _IpRegistry.RegisterDevice(cls, newName)
        
    
    def __init__(self, carrier, ipslot, cardid=None, interrupts=1):
        '''Every IP device is attached to a specific carrier card in a
        specified ipslot.  By default an EPICS card id and one interrupt
        are allocated.'''
        
        self.__super.__init__()

        assert 0 <= ipslot < carrier.MaxIpSlots, 'Invalid IP slot: %d' % ipslot
        assert carrier.ip_support, 'Carrier card not configured for IP cards'
        
        # The standard algorithm for assigning card identifers is used.  This
        # can be overridden by the caller, but shouldn't normally be.
        if cardid == None:
            cardid = 10 * carrier.slot + ipslot
        self.IPACid = carrier.IPACid
        self.ipslot = ipslot
        self.cardid = cardid
        self.carrier = carrier

        # Allocate one or more interrupt vectors as required.
        if interrupts:
            self.vector = self.AllocateIntVector(interrupts)

    def ipmIrqCmd(self, irq, cmd):
        '''This generates a call to ipmIrqCmd for this slot.'''
        self.carrier.ipmIrqCmd(self.ipslot, irq, cmd)
