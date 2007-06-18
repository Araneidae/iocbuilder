import os.path

from _epics import *
from asyn import AsynSerial

__all__ = ['streamProtocol']


class streamBus(Device):
    ModuleName = 'streamDevice'
    LibFileList = ['streamLib', 'streamTty.o']
    DbdFileList = ['stream.dbd']
    LibFileList__3_14 = ['stream']

    # The set of protocol directories is remembered as a set.
    ProtocolDirs = set()
    
    def __init__(self, protocolDir, port):
        self.__super.__init__()
        self.ProtocolDirs.add(protocolDir)
        self.port = port

    def InitialiseOnce(self):
        # Version 1 of the streams library only supports one protocol
        # directory
        assert len(self.ProtocolDirs) == 1, \
            'Inconsistent protocol directories %s' % repr(self.ProtocolDirs)
        print 'STREAM_PROTOCOL_DIR = "%s"' % self.ProtocolDirs.pop()

    def Initialise__3_13(self):
        print '%s_streamBus = "Tty"' % self.port

        

class streamProtocol(ModuleBase):
#     # Default path within component to protocol directory.  This is the
#     # standard path for EPICS 3.14 builds at Diamond.
    ProtocolPath = 'data'

#    def __init__(self, port, ProtocolName = None, ProtocolFile = None):
    def __init__(self, port):
        self.__super.__init__()
#         if ProtocolName is None:  ProtocolName = self.ProtocolName
#         if ProtocolFile is None:  ProtocolFile = self.ProtocolFile

        path = self.LibPath()
        if self.ProtocolPath:
            path = os.path.join(path, self.ProtocolPath)

        self.port = port.DeviceName()
        if Configure.EpicsVersion == '3_13':
            self.port = self.port[1:].replace('/', '_')
        streamBus(path, self.port)

        # Build the record factories for this channel
        for list, link in (
                (self.__InRecords, 'INP'),
                (self.__OutRecords, 'OUT')):
            for record in list:
                setattr(self, record, RecordFactory(
                    getattr(records, record), 'stream', link, self._address))


    # Record factory support
    def _address(self, fields, command, *protocol_args):
        if protocol_args:
            command = '%s(%s)' % (command, ','.join(map(str, protocol_args)))
        return '@%s %s %s' % (self.ProtocolName, command, self.port)

    # Lists of input and output records to generate factories for
    __InRecords = [
        'ai', 'bi', 'mbbi', 'mbbiDirect', 'longin', 'stringin', 'waveform']
    __OutRecords = [
        'ao', 'bo', 'mbbo', 'mbboDirect', 'longout', 'stringout']

