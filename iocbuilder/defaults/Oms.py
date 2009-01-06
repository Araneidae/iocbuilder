from iocbuilder import *
from asyn import Asyn
from seq import Seq


__all__ = ['MotorLib', 'OmsVme58']



class MotorLib(Device):
    ModuleName = 'motor'
    Dependencies = (Asyn, Seq)
    
    LibFileList = ['motor', 'softMotor']
    DbdFileList = ['motorSupport.dbd', 'devSoftMotor.dbd']



class OmsVme58(Device):
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

    ModuleName = MotorLib.ModuleName
    
    Dependencies = (MotorLib,)
    DbdFileList = ['devOms.dbd']
    LibFileList = ['oms']
        
        
    # The initialisation and configuration of OMS Vme58 motor controller
    # cards is a little fiddly.  The base address of each card is set by
    # means of jumpers, and each card is allocated its own interrupt vector,
    # but the driver initialisation routine, oms58Setup, only takes the
    # lowest base address and vector as argument!
    #
    # As a consequence, we need to know all of the OMS cards before we create
    # any card resources.  We manage this by requiring that channel only be
    # called after all instances of this class have been created.  This
    # entails keeping some state within the class itself


    # Here we remember the global state for the OMS card
    class __OmsState:
        def __init__(self, pollrate, intlevel):
            # We remember all the cards that have been allocated.
            self.CardSet = set()
            self.pollrate = pollrate
            self.intlevel = intlevel

            # ...
            self.Fresh = True

        def AddCard(self, baseaddress):
            assert self.Fresh, \
                'Channel already allocated: cannot create new OMS card'
            assert baseaddress not in self.CardSet, 'Card already defined'
            self.CardSet.add(baseaddress)

        # This is called once we know that we are done allocating OMS class
        # instances: we now know that every card has been declared.  We can
        # now compute the base address and can now allocate card identifiers.
        def InitialiseBaseAddress(self):
            if self.Fresh:
                self.Fresh = False
                self.BaseAddress = min(self.CardSet)
                self.CardCount = len(self.CardSet)
                assert self.CardCount == 1 + self.CardId(max(self.CardSet)), \
                    'Card addresses not allocated contiguously'
                self.Vector = Device.AllocateIntVector(self.CardCount)

        # Converts a card address into a card id
        def CardId(self, baseaddress):
            assert not self.Fresh
            return (baseaddress - self.BaseAddress) / 0x1000
        
    
    def __init__(self, baseaddress=0xf000, axes=8, pollrate=10, intlevel=5):
        '''The base address for each card must match the address jumpered into
        the corresponding card to be controlled.
            Only 8 or 4 axis cards are supported: the number of axes should
        match the type of controller card, not the particular details of the
        installation.
            If a non default pollrate or intlevel are specified, then the same
        value must be specified for all cards.'''
        
        if not hasattr(OmsVme58, 'State'):
            OmsVme58.State = self.__OmsState(pollrate, intlevel)
        
        self.__super.__init__()
        assert axes == 8 or axes == 4, 'Invalid number of axes'
        assert baseaddress & 0xf000 == baseaddress, 'Invalid base address'
        assert pollrate == self.State.pollrate, 'Inconsistent poll rate'
        assert intlevel == self.State.intlevel, 'Inconsistent interrupt level'

        # For the moment all we can do is remember the card we've been given.
        self.axes = axes
        self.baseaddress = baseaddress
        self.State.AddCard(baseaddress)


    def channel(self, channel):
        '''Access channel for controlling one of the motors supported by this
        card.'''
        self.State.InitialiseBaseAddress()
        assert 0 <= channel < self.axes, \
               'Channel %d out of range' % channel
        return _OmsVme58Channel(self.State.CardId(self.baseaddress), channel)
    

    def InitialiseOnce(self):
        '''Internal method'''
        # Only generate initialisation if this the first call to Initialise.
        # Otherwise reset the state so that we can reuse this class for
        # another IOC.
        print 'oms58Setup(' \
            '%(CardCount)d, 0x%(BaseAddress)x, %(Vector)d, ' \
            '%(intlevel)d, %(pollrate)d)' % self.State.__dict__
        del OmsVme58.State
        

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
    
