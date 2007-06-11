from IpCarrier import IpDevice
from _epics import *
from baselib import mbbi32Direct, Sscan


class DLS8512(IpDevice):
    Dependencies__3_14 = (Sscan,)
    Dependencies__3_13 = (mbbi32Direct,)

    LibFileList = ['DLS8512Lib']
    DbdFileList = ['DLS8512.dbd']
    
    LibFileList__3_14 = ['DLS8512Support']
    DbdFileList__3_14 = ['DLS8512support.dbd']

    def __init__(self, carrier, ipslot, cardid=None,
                 timer=False, ignoreoverflow=True):
        self.__super.__init__(carrier, ipslot, cardid)

        # The two features of interest supported by this card are whether
        # register 15 is an automatic timer and whether counters stop or
        # automatically continue when they overflow.
        self.features = ((not timer) << 0) | (ignoreoverflow << 2)

    def Initialise(self):
        print 'DLS8512Configure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d, ' \
            '%(features)d)' % self.__dict__

    def channel(self, channel):
        return _DLS8512channel(self, channel)


class _DLS8512channel:
    def __init__(self, scaler, channel):
        assert 0 <= channel  and  channel < 16, 'Channel out of range'
        address = '#C%d S%d @' % (scaler.cardid, channel)

        # Reads the current value of the selected counter channel
        self.ai = RecordFactory(records.ai, 'DLS8512', 'INP', address)
        # Writes a new value into the selected counter
        self.ao = RecordFactory(records.ao, 'DLS8512', 'OUT', address)
        # Resets the entire counter card.  The channel is ignored
        self.bo = RecordFactory(records.bo, 'DLS8512', 'OUT', address)
