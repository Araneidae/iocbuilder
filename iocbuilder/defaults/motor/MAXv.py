from iocbuilder import Device, records, RecordFactory

from Oms import OmsVme

__all__ = ['OmsMAXv']



class OmsMAXv(OmsVme):

    def __init__(self,
            baseaddress = 0xf000, axis_count = 8, pollrate = 10, intlevel = 5,
            address_space = 16):
        '''The base address for each card must match the address jumpered into
        the corresponding card to be controlled.
            Only 8 or 4 axis cards are supported: the number of axes should
        match the type of controller card, not the particular details of the
        installation.
            If a non default pollrate or intlevel are specified, then the same
        value must be specified for all cards.'''

        assert axis_count == 8 or axis_count == 4, 'Invalid number of axes'

        # For each valid choice of address map, the corresponding addressing
        # intervals are specified here.
        AddressMap = { 16: 0x1000, 24: 0x10000, 32: 0x1000000 }
        self.__super.__init__(AddressMap[address_space], baseaddress,
            pollrate = pollrate, intlevel = intlevel)
        
        self.address_space = address_space
        self.axis_count = axis_count

        self.Axes = {}


    def channel(self, channel, **kargs):
        '''Access channel for controlling one of the motors supported by this
        card.'''
        self.InitialiseBaseAddress()
        assert 0 <= channel < self.axis_count, \
               'Channel %d out of range' % channel
        return _OmsMAXvChannel(self, channel, **kargs)

    def _AddAxis(self, name, limit, servo):
        assert name not in self.Axes, 'Axis %s already defined' % name
        assert len(self.Axes) < self.axis_count, 'Too many axes'
        self.Axes[name] = (limit, servo)
    

    def InitialiseOnce(self):
        self.InitialiseBaseAddress()
        print 'MAXvSetup(' \
            '%(CardCount)d, %(address_space)d, 0x%(BaseAddress)x, ' \
            '%(Vector)d, %(intlevel)d, %(pollrate)d)' % self.CardSetDict()

    def Initialise(self):
        print 'MAXvConfig(%d, "%s")' % (
            self.CardId(),
            '; '.join([
                'A%s L%s %s' % (name, limit, servo) for
                name, (limit, servo) in self.Axes.items()]))
        

class _OmsMAXvChannel:
    def __init__(self, card, channel, limit='H', servo='PSM'):
        '''Servo is one of:
            PSM : servo axis
            PSE : stepper with encoder
            PSO : stepper open loop

        Limit is one of:
            H: active high limit switches
            L: active low limit switches
        '''        
        assert limit in 'HL', 'Invalid limit switch time %s' % limit
        assert servo in ['PSM', 'PSE', 'PSO'], 'Invalid servo type %s' % servo

        self.card = card
        self.cardid = 0
        self.channel = channel
        
        card._AddAxis(self.AxisName(), limit, servo)

        address = '#C%d S%d' % (self.cardid, channel)
        self.motor = RecordFactory(records.motor, 'OMS VME58', 'OUT', address)


    def CardId(self):
        return self.cardid

    def ChannelId(self):
        return self.channel

    def AxisName(self):
        return 'XYZTUVRS'[self.channel]
