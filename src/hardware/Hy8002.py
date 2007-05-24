# Hardware definitions for 8002 and IP cards

from IpCarrier import IpCarrier


__all__ = ['Hy8002']


# ----------------------------------------------------------------------
#   Hytec 8002 IP carrier card


# General purpose carrier card
class Hy8002(IpCarrier):
    # This device supports up to 4 IP cards.
    MaxIpSlots = 4
    
    def __init__(self, slot, intLevel = 2, swapint = None):
        self.__super.__init__(slot)

        self.intLevel = intLevel
        if swapint is None:
            swapint = self.defaultSwapInterrupt
        self.swapint = swapint


    @classmethod
    def AddedToLibrary(cls):
        # In general we share the hot-swap interrupt for the 8002 among all
        # instances: this interrupt isn't actually used (no real driver
        # support) but must be allocated anyway to avoid an error message.
        cls.defaultSwapInterrupt = cls.AllocateIntVector()
    

    # Loading the ipac library is enough to load the libraries for this
    # card.
    def Initialise(self):
        # The only initialisation an 8002 needs is to initialise the carrier.
        self.InitialiseCarrier(
            'EXTHy8002', self.slot, self.intLevel, self.swapint)
