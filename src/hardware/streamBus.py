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
    
    def __init__(self, protocolDir):
        self.__super.__init__()
        self.ProtocolDirs.add(protocolDir)

    def InitialiseOnce(self):
        # Version 1 of the streams library only supports one protocol
        # directory
        assert len(self.ProtocolDirs) == 1, \
            'Inconsistent protocol directories %s' % repr(self.ProtocolDirs)
        print 'STREAM_PROTOCOL_DIR = "%s"' % self.ProtocolDirs.pop()



class streamProtocol(Device):
    Dependencies__3_14 = (AsynSerial,)
    
    # Default path within component to protocol directory.  This is the
    # standard path for EPICS 3.14 builds at Diamond.
    ProtocolPath = 'data'

    def __init__(self, port):
        self.__super.__init__()

        path = self.LibPath()
        if self.ProtocolPath:
            path = os.path.join(path, self.ProtocolPath)
        streamBus(path)

        self.port = port.DeviceName()
        self.__FixupPort()

        # Build the record factories for this channel
        for list, link in (
                (self.__InRecords, 'INP'),
                (self.__OutRecords, 'OUT')):
            for record in list:
                setattr(self, record, RecordFactory(
                    getattr(records, record), 'stream', link, self._address))

    def __FixupPort(self): pass
    def __FixupPort__3_13(self):
        self.port = self.port[1:].replace('/', '_')

    def Initialise__3_13(self):
        print '%s_streamBus = "Tty"' % self.port

#     def Initialise__3_14(self):
#         print 'drvAsynSerialPortConfigure("%s", "%s", 0, 0, 0)' % (
#             self.port, self.raw_port)


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

