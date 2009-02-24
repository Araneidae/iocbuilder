# Hardware implementation for 8001 digital IO card.

from iocbuilder import records, RecordFactory
from IpCarrier import IpCarrier


# List of standard names to be exported
__all__ = [ 'Hy8001',  'DIRECTION_INPUT', 'DIRECTION_OUTPUT' ]


# ----------------------------------------------------------------------
#   Hytec 8001 dedicated digital I/O card


DIRECTION_INPUT  = 0  # All bits inputs
DIRECTION_OUTPUT = 1  # All bits outputs
DIRECTION_MIXED  = 2  # Mixed ??? -- not supported in this code at present

# Dedicated 64-bit digital IO card
class Hy8001(IpCarrier):
    DbdFileList = ['Hy8001']
    
    # An 8002 supports two IP slots.  Note that using these for IP cards is
    # mutually exclusive with using ports A and B for digital I/O.
    MaxIpSlots = 2
    ArgInfo = [
        ('slot', int, 'VME Slot number'),
        ('direction', int, '0 for input, 1 for output, 2 for mixed'),
        ('cardid', int, 'cardid?', None),
        ('intLevel', int, 'intLevel?', 0),
        ('clock', int, 'clock?', 0),
        ('scan', int, 'scan?', 0),
        ('invertin', int, 'invertin?', 0),
        ('invertout', int, 'invertout?', 0),
        ('ip_support', bool, 'ip_support?', False)
    ]    
    def __init__(self,
            slot, direction, cardid, intLevel, clock, scan, invertin,
            invertout, ip_support):
        self.__super.__init__(slot, ip_support)

        if not cardid: cardid = 10 * slot
        
        self.direction = direction
        self.cardid = cardid
        self.intLevel = intLevel
        self.clock = clock
        self.scan = scan
        self.direction = direction
        self.invertin = invertin
        self.invertout = invertout

        self.vector = self.AllocateIntVector()

        # Configure the bottom supported bit according to whether IP support
        # has been requested.
        if ip_support:
            # Reserve ports A & B for IP use only if IP carrier enabled.
            self.low_bit = 32 
        else:
            self.low_bit = 0

    # define the initialisation code and dbd support for the library.

    def Initialise(self):
        print 'Hy8001Configure(' \
            '%(cardid)d, %(slot)d, %(vector)d, %(intLevel)d, 0, 0, ' \
            '%(clock)d, %(scan)d, %(direction)d, ' \
            '%(invertin)d, %(invertout)d)' % self.__dict__
        self.InitialiseCarrier('EXTHy8001', self.slot)

    def register(self, offset, length):
        return _Hy8001register(self, offset, length)

    def bit(self, offset):
        return _Hy8001bit(self, offset)



class _Hy8001bit:
    def __init__(self, card, offset):
        assert card.low_bit <= offset and offset < 64, 'Bit out of range'
        address = '#C%d S%d @' % (card.cardid, offset)
        if card.direction == DIRECTION_INPUT:
            self.bi = RecordFactory(records.bi, 'Hy8001', 'INP', address)
        if card.direction == DIRECTION_OUTPUT:
            self.bo = RecordFactory(records.bo, 'Hy8001', 'OUT', address)



class _Hy8001register:
    def __init__(self, card, offset, length):
        assert card.low_bit <= offset and offset + length <= 64 and \
               0 < length, 'Register index out of range'
        assert offset + length <= 32 or 32 <= offset, \
            'Selected range overlaps low and high blocks'

        self.card = card
        self.offset = offset
        self.length = length

        # Take account of quirk in register addressing: the high and low
        # 32-bit words are treated independently.
        high = ''
        if offset >= 32:
            high = '1'
            offset -= 32
        address = '#C%d S%d @%s' % (card.cardid, offset, high)
        
        if card.direction == DIRECTION_INPUT:
            self.mbbiDirect = RecordFactory(
                records.mbbiDirect, 'Hy8001', 'INP', address, self._post)
            self.mbbi = RecordFactory(
                records.mbbi, 'Hy8001', 'INP', address, self._post)
        if card.direction == DIRECTION_OUTPUT:
            self.mbboDirect = RecordFactory(
                records.mbboDirect, 'Hy8001', 'OUT', address, self._post)
            self.mbbo = RecordFactory(
                records.mbbo, 'Hy8001', 'OUT', address, self._post)

    def _post(self, record):
        record.NOBT = self.length

    def bit(self, offset):
        assert 0 <= offset < self.length, 'Bit out of range'
        return self.card.bit(self.offset + offset)
    
    def register(self, offset, length):
        assert 0 <= offset and offset + length <= self.length, \
               'Subregister out of range'
        return _Hy8001register(self.card, self.offset + offset, length)
