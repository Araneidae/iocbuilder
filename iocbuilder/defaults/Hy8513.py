from iocbuilder import records, RecordFactory
from iocbuilder.modules.ipac import IpDevice


class Hy8513(IpDevice):
    DbdFileList = ['Hy8513']
    LibFileList = ['Hy8513']

    def Initialise(self):
        print 'Hy8513Configure(' \
            '%(cardid)d, %(IPACid)s, %(ipslot)d, %(vector)d)' \
            % self.__dict__

    def channel(self, channel):
        return _Hy8513channel(self, channel)


class _Hy8513channel:
    def __init__(self, encoder, channel):
        assert 0 <= channel  and  channel < 4, 'Channel out of range'
        address = '#C%d S%d @' % (encoder.cardid, channel)

        self.ai = RecordFactory(records.ai, 'Hy8513', 'INP', address)
        self.ao = RecordFactory(records.ao, 'Hy8513', 'OUT', address)
        self.bi = RecordFactory(records.bi, 'Hy8513', 'INP', address)
        self.bo = RecordFactory(records.bo, 'Hy8513', 'OUT', address)
