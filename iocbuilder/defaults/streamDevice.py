import os.path
from iocbuilder import Device, RecordFactory, IocDataFile, ModuleBase
from iocbuilder import records, hardware, quote_c_string

from asyn import AsynSerial


__all__ = [
    'streamProtocol', 'ProtocolFile', 'AutoProtocol',
    'streamDeviceVersion']


assert not hasattr(hardware, 'streamDeviceVersion'), \
    'Cannot mix stream device versions!'
streamDeviceVersion = 2


class streamDevice(Device):
    LibFileList = ['pcre', 'stream']
    DbdFileList = ['stream']
    AutoInstantiate = True


class streamProtocol(Device):
    Dependencies = (streamDevice,)

    def __init__(self, port, protocol):
        '''Each streamProtocol instance is constructed by binding a serial
        port to a protocol file.'''
        self.__super.__init__()

        # The new stream device requires that the stream be wrapped as an
        # asyn device.  We validate that wrapping here.
        assert getattr(port, 'IsAsyn', False), \
            'Stream Device port must be asyn port'
        self.port = port
        # Pick up the protocol name from the file name.
        self.ProtocolName = protocol.ProtocolName

        # Build the record factories for this channel
        for list, link in (
                (self.__InRecords,  'INP'),
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


class ProtocolFile(Device):
    Dependencies = (streamDevice,)

    # We'll need to post process the list of instances
    __ProtocolFiles = set()
    __ForceCopy = False

    @classmethod
    def ForceCopy(cls):
        cls.__ForceCopy = True

    def __init__(self, protocol_file, force_copy=False):
        self.__super.__init__()
        # Add to the set of protocol files and remember whether copying was
        # demanded.
        self.__ProtocolFiles.add(protocol_file)
        if force_copy:
            streamProtocol.__ForceCopy = True
        # Pick up the protocol name from the file name.
        self.ProtocolName = os.path.basename(protocol_file)

    def InitialiseOnce(self):
        # Figure out whether we need to copy the files.  If any protocol
        # needs to be copied or if we are trying to use more than one
        # protocol directory then copying is needed.  (We could specify a
        # protocol path instead, but this isn't implemented yet.)
        protocol_dirs = set(
            [os.path.dirname(file) for file in self.__ProtocolFiles])
        if self.__ForceCopy or len(protocol_dirs) > 1:
            protocol_dirs = [IocDataFile.GetDataPath()]
            for file in self.__ProtocolFiles:
                # Grab a copy of each data file.
                IocDataFile(file)
        print 'epicsEnvSet "STREAM_PROTOCOL_PATH", %s' % \
            quote_c_string(':'.join(protocol_dirs))

    def __str__(self):
        return self.ProtocolName


class AutoProtocol(ModuleBase):
    BaseClass = True

    @classmethod
    def UseModule(cls):
        # Automatically convert all protocol files into protocol instances
        # before the class is actually instantiated.
        cls.Protocols = [
            ProtocolFile(cls.ModuleFile(os.path.join('data', file)))
            for file in cls.ProtocolFiles]
        cls.__super.UseModule()
