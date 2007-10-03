from IpCarrier import IpDevice
from _epics import *



# Clock sample rates for ADC
CLOCK_1Hz = 0
CLOCK_2Hz = 1
CLOCK_5Hz = 2
CLOCK_10Hz = 3
CLOCK_20Hz = 4
CLOCK_50Hz = 5
CLOCK_100Hz = 6
CLOCK_200Hz = 7
CLOCK_500Hz = 8
CLOCK_1kHz = 9
CLOCK_2kHz = 10
CLOCK_5kHz = 11
CLOCK_10kHz = 12
CLOCK_20kHz = 13
CLOCK_50kHz = 14
CLOCK_100kHz = 15


# Helper routine for consuming optional parameters.
def _ReadField(fields, key, param):
    result = ''
    if key in fields:
        result = ' %s=%d' % (param, fields[key])
        del fields[key]
    return result



class Hy8401(IpDevice):
    '''Hytec 8401 Analogue to Digital Converter (ADC).'''

    ModuleName = 'Hy8401ip'
    LibFileList = ['Hy8401ipLib']
    DbdFileList = ['Hy8401ip.dbd']

    LibFileList__3_14 = ['Hy8401ip']
        
    def __init__(self, carrier, ipslot, cardid=None,
                 intEnable = 0,              # No interrupts
                 externalClock = 0,          # Use internal clock
                 clockRate = CLOCK_100kHz,   #  running at 100kHz
                 inhibit = 0,                # Ignore front panel inhibit
                 sampleSize = 0):            # Disable triggered capture
        '''Optional arguments are:
        intEnable     Set to 1 to enable interrupts
        externalClock Set to 1 for external clock
        clockRate     Set clock rate (default 15), 0 => 1Hz, 15 => 100kHz
        inhibit       Set to 1 to enable front panel inhibit signal
        sampleSize    Set to number of samples for triggered capture
        '''

        assert intEnable in [0, 1], 'Invalid intEnable value'
        assert externalClock in [0, 1], 'Invalid externalClock value'
        assert clockRate in range(16), 'Invalid clock rate'
        assert inhibit in [0, 1], 'Invalid inhibit value'
        assert sampleSize >= 0, 'Invalid sample size'
        assert (sampleSize > 0) <= bool(intEnable), \
            'Triggered capture requires interrupts'

        self.__super.__init__(carrier, ipslot, cardid)
        
        self.intEnable = intEnable
        self.externalClock = externalClock
        self.clockRate = clockRate
        self.inhibit = inhibit
        self.sampleSize = sampleSize

        self.bo = RecordFactory(
            records.bo, 'Hy8401ip', 'OUT', '#C%d S0' % self.cardid)

    def InitialiseOnce(cls):
        print 'Hy8401ip32bit()'

    def Initialise(self):
        print 'Hy8401ipConfigure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d, ' \
            '%(intEnable)d, 0, %(externalClock)d, %(clockRate)d, ' \
            '%(inhibit)d, 1, 1, %(sampleSize)d)' % self.__dict__

    def channel(self, channel):
        return _ADCchannel(self, channel)



# A single ADC channel on an ADC.  This class remembers all the information
# required to create records to read from the adc
class _ADCchannel:
    def __init__(self, adc, channel):
        assert 0 <= channel  and  channel < 8, 'Channel out of range'
        self.adc = adc
        self.card = adc.cardid
        self.channel = channel

        self.ai = RecordFactory(
            records.ai, 'Hy8401ip', 'INP', self._ai_address)
        self.waveform = RecordFactory(
            records.waveform, 'Hy8401ip', 'INP', self._waveform_address)

    def SampleSize(self):
        '''Returns number of samples for triggered capture or 0 if continuous
        capture enabled instead.'''
        return self.adc.sampleSize

    def _ai_address(self, fields):
        params = \
            _ReadField(fields, 'offset', 'OFFSET') + \
            _ReadField(fields, 'mean', 'MEAN')
        return '#C%d S%d @%s' % (self.adc.cardid, self.channel, params)

    def _waveform_address(self, fields):
        params = _ReadField(fields, 'offset', 'OFFSET') 
        return '#C%d S%d @%s' % (self.adc.cardid, self.channel, params)
