from iocbuilder import records, RecordFactory
from iocbuilder.modules.ipac import IpDevice


class Hy8505(IpDevice):
    '''16 bit digital IO device.'''

    LibFileList = ['Hy8505']
    DbdFileList = ['Hy8505']

    def __init__(self, carrier, ipslot, 
            direction=0,            # All bits inputs
            debounce_rate=0,        # Debounce rate, 0 => no debounce
            debounce_mask=0xFFFF,   # Bits to debounce
            scanrate=3,             # 1MHz input scan
            interrupt_mask=0,       # Input bits to generate interrupts
            pulse_width=3,          # Pulse width 1 second
            pulse_mask=0,           # Bits to pulse
            clock=0,                # Internal clock
            invertin=False,
            invertout=False, cardid=None):
        '''Parameters for 8505.

        debounce_rate   Select input debounce clock
            0 => no debounce
            1 => 100Hz      2 => 200Hz      3 => 500Hz      4 => 1kHz
        debounce_mask   Select input bits to be debounced
        scanrate        Select input scan rate
            0 => 1kHz       1 => 10kHz      2 => 100kHz     3 => 1MHz
        direction       Selects input and output directions
            0 => All bits are inputs
            1 => Bits 0-7 outputs, bits 8-15 inputs
            2 => Bits 0-7 inputs, bits 8-15 outputs
            3 => All bits are outputs
        interrupt_mask  Select which input bits generate interrupts
        pulse_width     Select width of pulsed outputs
            0 => 1ms        1 => 10ms       2 => 100ms      3 => 1s
            4 => 2s         5 => 5s         6 => 10s        7 => 20s
            8 => 50s        9 => 100s
        pulse_mask      Select which output bits generate pulsed outputs
        clock           Select internal or external clock
            0 => internal clock     1 => external clock
        invertin        If set then all input bits will be inverted
        invertout       If set then all output bits will be inverted

        Note that invertout will not change the way in which the hardware
        handles pulsed outputs.  In particular, when invertout is set it is
        necessary to write 0 to a pulsed output to generate a pulse.
        '''

        # Support textual specification of certain particular important
        # values.
        if not isinstance(direction, int):
            direction = {'II' : 0, 'IO' : 1, 'OI' : 2, 'OO' : 3}[direction]

        assert 0 <= debounce_rate <= 4, 'Invalid debounce rate'
        assert 0 <= debounce_mask <= 0xFFFF, 'Invalid debounce mask'
        assert 0 <= scanrate <= 3, 'Invalid scan rate'
        assert 0 <= direction <= 3, 'Invalid direction'
        assert 0 <= interrupt_mask <= 0xFFFF, 'Invalid interrupt mask'
        assert 0 <= pulse_width <= 8, 'Invalid pulse width'
        assert 0 <= pulse_mask <= 0xFFFF, 'Invalid pulse mask'
        assert 0 <= clock <= 1, 'Invalid clock'
        
        self.__super.__init__(carrier, ipslot, cardid)

        # Build a mask representing the direction of each bit in the
        # register.
        self.directionMask = \
            (direction & 1 and 0xFF) | (direction & 2 and 0xFF00)

        # Accumulate directions onto the direction argument
        if invertin:    direction |= 4
        if invertout:   direction |= 8

        # Remember arguments for device initialisation
        self.debounce_rate = debounce_rate
        self.debounce_mask = debounce_mask
        self.scanrate = scanrate
        self.direction = direction
        self.interrupt_mask = interrupt_mask
        self.pulse_width = pulse_width
        self.pulse_mask = pulse_mask
        self.clock = clock
        self.invertin = invertin
        self.invertout = invertout


    def Initialise(self):
        print 'Hy8505Configure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, ' \
            '%(debounce_rate)d, %(pulse_width)d, %(scanrate)d, ' \
            '%(direction)d, %(vector)d, %(clock)d)' % self.__dict__
        print 'Hy8505ExtraConfig(' \
            '%(cardid)d, %(debounce_mask)d, %(pulse_mask)d, ' \
            '%(interrupt_mask)d)' % self.__dict__

    def register(self, offset, length):
        return _Hy8505register(self, offset, length)

    def bit(self, offset):
        return _Hy8505bit(self, offset)



class _Hy8505bit:
    def __init__(self, card, offset):
        assert 0 <= offset and offset < 16, 'Bit out of range'
        address = '#C%d S%d @' % (card.cardid, offset)
        # This bit supports either bi or bo depending on its direction.
        if card.directionMask & (1 << offset):
            self.bo = RecordFactory(records.bo, 'Hy8505', 'OUT', address)
        else:
            self.bi = RecordFactory(records.bi, 'Hy8505', 'INP', address)



class _Hy8505register:
    def __init__(self, card, offset, length):
        assert 0 <= offset and offset + length <= 16 and 0 < length, \
            'Register index out of range'
        # Compute which bits we're controlling, which of them are output
        # bits, and check that all bits go in the same direction!
        registerBits = (1 << length) - 1 << offset
        outputBits = registerBits & card.directionMask
        assert outputBits == 0 or outputBits == registerBits, \
            'Mixed input and output bits in register'

        self.card = card
        self.offset = offset
        self.length = length

        address = '#C%d S0 @' % card.cardid
        
        if outputBits:
            self.mbboDirect = RecordFactory(
                records.mbboDirect, 'Hy8505', 'OUT', address, self._post)
            self.mbbo = RecordFactory(
                records.mbbo, 'Hy8505', 'OUT', address, self._post)
        else:
            self.mbbiDirect = RecordFactory(
                records.mbbiDirect, 'Hy8505', 'INP', address, self._post)
            self.mbbi = RecordFactory(
                records.mbbi, 'Hy8505', 'INP', address, self._post)

    def _post(self, record):
        record.NOBT = self.length
        record.SHFT = self.offset

    def bit(self, offset):
        assert 0 <= offset < self.length, 'Bit out of range'
        return self.card.bit(self.offset + offset)
    
    def register(self, offset, length):
        assert 0 <= offset and offset + length <= self.length, \
               'Subregister out of range'
        return _Hy8505register(self.card, self.offset + offset, length)
