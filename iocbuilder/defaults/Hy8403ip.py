from iocbuilder import records, RecordFactory, Substitution
from iocbuilder.hardware import IpDevice

__all__ = ['Hy8403ipTemplate']


# 24 bit serial ADC
class Hy8403(IpDevice):
    DbdFileList = ['Hy8403ip']
    LibFileList = ['Hy8403ip']
    
    def __init__(self, carrier, ipslot, cardid=None,
            aitype=0, memsize = 1, clockSource=0, clockRate=200,
            gain = 1, vref = 1):
        self.__super.__init__(carrier, ipslot, cardid)

        assert aitype in range(6), 'Invalid input type'
        assert memsize in [1, 2], 'Invalid memory size'
        assert clockSource in [0, 1], 'Invalid clock source'
        assert clockRate in [1, 2, 5, 10, 20, 50, 100, 200], \
            'Invalid clock rate'
        assert gain in [1, 2, 4, 8, 16, 32, 64, 128], \
            'Invalid gain setting'
        assert vref in [1, 2], 'Invalid vref'
        
        self.aitype = aitype
        self.memsize = memsize
        self.clockSource = clockSource
        self.clockRate = clockRate
        self.gain = gain
        self.vref = vref

        # Compute the number of channels from the input type.
        if aitype == 0:
            # Differential input mode
            self.channelCount = 8
        else:
            # Various single ended modes (thermocouples or PT-100)
            self.channelCount = 16

    def Initialise(self):
        print 'Hy8403Configure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d, ' \
            '%(aitype)d, %(memsize)d, %(clockSource)d, %(clockRate)d, ' \
            '%(gain)d, %(vref)d)' % \
                self.__dict__

    def channel(self, channel):
        return _ADCchannel(self, channel)


# A single ADC channel.  This class remembers all the information
# required to create records to read from the adc
class _ADCchannel:
    def __init__(self, adc, channel):
        assert 0 <= channel  and  channel < adc.channelCount, \
            'Channel %d out of range' % channel
        
        address = '#C%d S%d @' % (adc.cardid, channel)
        self.ai = RecordFactory(records.ai, 'Hy8403ai', 'INP', address)
        self.ao = RecordFactory(records.ao, 'Hy8403ao', 'OUT', address)


class Hy8403ipTemplate(Substitution):
    Arguments = ('device', 'card')
    TemplateFile = 'Hy8403ip.template'

