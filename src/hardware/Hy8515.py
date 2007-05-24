from _epics import Device
from IpCarrier import IpDevice


class Hy8515(IpDevice):
    LibFileList = ['drvHy8515.o']
    LibFileList__3_14 = ['drvHy8515']
    DbdFileList__3_14 = ['Hy8515.dbd']
    
    def __init__(self, carrier, ipslot, cardid=None,
                 intdelay = -32, halfduplex = 0, delay845 = 0):
        self.__super.__init__(carrier, ipslot, cardid)

        # Default device parameters, can be overwritten by keyword arguments.
        self.intdelay = intdelay
        self.halfduplex = halfduplex
        self.delay845 = delay845
        
        self.cardname = 'CARD%d' % self.cardid

    def Initialise(self):
        print '%(cardname)s = Hy8515Configure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d, ' \
            '%(intdelay)d, %(halfduplex)d, %(delay845)d)' % self.__dict__

    def channel(self, *pargs, **kargs):
        return _Hy8515channel(self, *pargs, **kargs)


class _Hy8515channel(Device):
    ModuleName = Hy8515.ModuleName
    
    def __init__(self, card, channel, 
                 readbuf = 2500,
                 writebuf = 250,
                 speed = 9600,
                 parity = 'N',
                 stopbits = 1,
                 numbits = 8,
                 flowctrl = 'N'):

        self.__super.__init__()
        assert 0 <= channel  and  channel < 8, 'Channel out of range'

        self.channel = channel

        self.readbuf = readbuf
        self.writebuf = writebuf
        self.speed = speed
        self.parity = parity
        self.stopbits = stopbits
        self.numbits = numbits
        self.flowctrl = flowctrl

        self.cardname = card.cardname
        self.portname = 'PORT%d_%d' % (card.cardid, channel)
        self.device = '/ty/%d/%d' % (card.cardid, channel)

    def SetParameters(self,
            speed=None, parity=None, stopbits=None,
            numbits=None, flowctrl=None):
        if speed is not None:       self.speed = speed
        if parity is not None:      self.parity = parity
        if stopbits is not None:    self.stopbits = stopbits
        if numbits is not None:     self.numbits = numbits
        if flowctrl is not None:    self.flowctrl = flowctrl

    def Initialise(self):
        print '%(portname)s = tyHYOctalDevCreate(' \
            '"%(device)s", %(cardname)s, %(channel)d, ' \
            '%(readbuf)d, %(writebuf)d)' % self.__dict__
        print 'tyHYOctalConfig(' \
            '%(portname)s, %(speed)d, \'%(parity)c\', %(stopbits)d, ' \
            '%(numbits)d, \'%(flowctrl)c\')' % self.__dict__

    # Returns the associated device name.
    def DeviceName(self):
        return self.device



# The 8516 is identical to the 8515, so just clone it.
Hy8515.Clone('Hy8516')
