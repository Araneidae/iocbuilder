from iocbuilder import records, RecordFactory
from iocbuilder.modules.ipac import IpDevice


# Digital to Analogue convert (DAC)
class Hy8402(IpDevice):
    DbdFileList = ['Hy8402ip']
    LibFileList = ['Hy8402ip']
    
    def __init__(self, carrier, ipslot, cardid=None,
            doram=0, clockSource=0, clockRate=15, inhibit=0):
        self.__super.__init__(carrier, ipslot, cardid)

        self.doram = doram
        self.clockSource = clockSource
        self.clockRate = clockRate
        self.inhibit = inhibit

    def Initialise(self):
        print 'Hy8402ipConfigure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d, ' \
            '%(doram)d, %(clockSource)d, %(clockRate)d, %(inhibit)d)' % \
                self.__dict__

    def channel(self, channel):
        return _DACchannel(self, channel)


# A single DAC channel on a DAC.  This class remembers all the information
# required to create records to read from the adc
class _DACchannel:
    def __init__(self, dac, channel):
        assert 0 <= channel  and  channel < 16, 'Channel out of range'
        address = '#C%d S%d @' % (dac.cardid, channel)
        self.ao = RecordFactory(records.ao, 'Hy8402ip', 'OUT', address)
