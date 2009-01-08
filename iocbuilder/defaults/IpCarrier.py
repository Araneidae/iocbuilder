# Generic support for IP carriers.  Only 8001 and 8002 cards exist as IP
# carriers, but a generic form of support is provided here.

import new
from iocbuilder import *

__all__ = ['IpDevice']


# All IP carriers, in particular both the 8001 and 8002, depend on the ipac
# library.  This device has no instances of its own.
class ipacLib(Device):
    '''IP carrier support library.'''
    DbdFileList = ['drvIpac.dbd']
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

        # Allocate one or more interrupt vectors as required.
        if interrupts:
            self.vector = self.AllocateIntVector(interrupts)
