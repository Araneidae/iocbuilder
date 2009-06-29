# Hardware definitions for 8002 and IP cards

from IpCarrier import IpCarrier, makeArgInfo

__all__ = ['Hy8002']


# ----------------------------------------------------------------------
#   Hytec 8002 IP carrier card


# General purpose carrier card
class Hy8002(IpCarrier):
    # This device supports up to 4 IP cards.
    MaxIpSlots = 4
    
    def __init__(self, slot, intLevel=2):
        self.__super.__init__(slot)
        self.intLevel = intLevel
    ArgInfo = makeArgInfo(__init__,
        slot     = (int, 'VME Slot number'),
        intLevel = (int, 'VME Interrupt Level'))
        

    @classmethod
    def UseModule(cls):
        cls.__super.UseModule()
        # In general we share the hot-swap interrupt for the 8002 among all
        # instances: this interrupt isn't actually used (no real driver
        # support) but must be allocated anyway to avoid an error message.
        cls.swapint = cls.AllocateIntVector()

    # Loading the ipac library is enough to load the libraries for this
    # card.
    def Initialise(self):
        # The only initialisation an 8002 needs is to initialise the carrier.
        self.InitialiseCarrier(
            'EXTHy8002', self.slot, self.intLevel, self.swapint)
