from iocbuilder import Device, records, RecordFactory
from iocbuilder.modules.asyn import Asyn

__all__ = ['MotorLib', 'OmsVme58']


class MotorLib(Device):
    Dependencies = (Asyn,)
    LibFileList = ['motor', 'softMotor']
    DbdFileList = ['motorSupport', 'devSoftMotor']
    AutoInstantiate = True

class OmsVme(Device):
    Dependencies = (MotorLib,)
    DbdFileList = ['devOms']
    LibFileList = ['oms']


    # The initialisation and configuration of OMS VME motor controller cards
    # is a little fiddly.  The base address of each card is set by means of
    # jumpers, and each card is allocated its own interrupt vector, but the
    # driver initialisation routine only takes the lowest base address and
    # vector as argument!
    #
    # As a consequence, we need to know all of the OMS cards before we create
    # any card resources.  We manage this by requiring that channel only be
    # called after all instances of this class have been created.  This
    # entails keeping some state within the class itself
    class __CardSet:
        def __init__(self, address_step, attributes):
            # We remember all the cards that have been allocated.
            self.CardSet = set()

            self.address_step = address_step
            self.attributes = attributes

            # Records whether the base address has been allocated.  After
            # this point no more cards can be added.
            self.Allocated = False

        def AddCard(self, baseaddress, attributes):
            assert not self.Allocated, \
                'Channel already allocated: cannot create new OMS card'
            assert baseaddress not in self.CardSet, 'Card already defined'
            assert baseaddress & ~(self.address_step-1) == baseaddress, \
                'Invalid base address: %x' % baseaddress
            assert self.attributes == attributes, \
                'Inconsistent card properties'
            self.CardSet.add(baseaddress)

        # This is called once we know that we are done allocating OMS class
        # instances: we now know that every card has been declared.  We can
        # now compute the base address and can now allocate card identifiers.
        def InitialiseBaseAddress(self):
            if not self.Allocated:
                self.Allocated = True
                self.BaseAddress = min(self.CardSet)
                self.CardCount = len(self.CardSet)
                max_id = self.CardId(max(self.CardSet))
                assert self.CardCount == 1 + max_id, \
                    'Card addresses not allocated contiguously'
                self.Vector = Device.AllocateIntVector(self.CardCount)

        # Converts a card address into a card id
        def CardId(self, baseaddress):
            assert self.Allocated
            return (baseaddress - self.BaseAddress) / self.address_step

        def CardSetDict(self, dictionary):
            return dict(dictionary, **dict(self.__dict__, **self.attributes))


    _CardSet = None

    def __init__(self, address_step, address, **attributes):
        self.__super.__init__()
        
        if not self._CardSet:
            # The CardSet is shared among all instances of each particular
            # sub-class, so we attach the new CardSet to the underlying
            # class.  This will now be picked up properly by self. reference.
            self.__class__._CardSet = self.__CardSet(address_step, attributes)
        self.baseaddress = address
        self._CardSet.AddCard(address, attributes)

    def CardId(self):
        return self._CardSet.CardId(self.baseaddress)

    def InitialiseBaseAddress(self):
        self._CardSet.InitialiseBaseAddress()

    def CardSetDict(self):
        return self._CardSet.CardSetDict(self.__dict__)



class OmsVme58(OmsVme):
    '''For each OMS-58 card a separate base address must be configured by
    setting jumpers on J61: note that the presence of a jumper implies a bit
    value of 0, so that the default state of no jumpers for A12, A13, A14 and
    A15 gives a default base address of 0xF000.
        Note further that the base addresses for different cards must be
    contiguous, as the driver will attempt to initialise all cards in the
    allocated block.

    So that the OmsVme58 device is able to correctly allocate card addresses,
    it is necessary to create all OmsVme85 instances before creating any
    channels.  This convention is enforced by this class.
    '''

    def __init__(self, baseaddress=0xf000, axes=8, pollrate=10, intlevel=5):
        '''The base address for each card must match the address jumpered into
        the corresponding card to be controlled.
            Only 8 or 4 axis cards are supported: the number of axes should
        match the type of controller card, not the particular details of the
        installation.
            If a non default pollrate or intlevel are specified, then the same
        value must be specified for all cards.'''
        self.__super.__init__(0x1000, baseaddress,
            pollrate = pollrate, intlevel = intlevel)
        
        assert axes == 8 or axes == 4, 'Invalid number of axes'
        self.axes = axes


    def channel(self, channel):
        '''Access channel for controlling one of the motors supported by this
        card.'''
        self.InitialiseBaseAddress()
        assert 0 <= channel < self.axes, \
               'Channel %d out of range' % channel
        return _OmsVme58Channel(self.CardId(), channel)
    

    def InitialiseOnce(self):
        # A single setup command initialises all installed cards.
        self.InitialiseBaseAddress()
        print 'oms58Setup(' \
            '%(CardCount)d, 0x%(BaseAddress)x, %(Vector)d, ' \
            '%(intlevel)d, %(pollrate)d)' % self.CardSetDict()
        

class _OmsVme58Channel:
    def __init__(self, cardid, channel):
        self.cardid = cardid
        self.channel = channel
        
        address = '#C%d S%d' % (cardid, channel)
        self.motor = RecordFactory(records.motor, 'OMS VME58', 'OUT', address)


    def CardId(self):
        return self.cardid

    def ChannelId(self):
        return self.channel

    def AxisName(self):
        return 'XYZTUVRS'[self.channel]
