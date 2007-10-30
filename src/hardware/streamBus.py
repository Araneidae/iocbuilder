import os.path
from _epics import *

from asyn import AsynSerial


__all__ = ['streamProtocol']


class streamProtocol(Device):
    ModuleName = 'streamDevice'
    LibFileList = ['streamLib', 'streamTty.o']
    DbdFileList = ['stream.dbd']
    LibFileList__3_14 = ['stream']

    # We'll need to post process the list of instances
    __ProtocolFiles = set()
    __ForceCopy = False

    def __init__(self, port, protocol_file, force_copy=False):
        '''Each streamProtocol instance is constructed by binding a serial
        port to a protocol file.
        '''
        self.__super.__init__()

        # Manage the global state.  Since version 1 of the stream protocol
        # doesn't support multiple protocol directories, we'll need to take a
        # copy of the protocol files if necessary.  Also, if copying is
        # forced then we'll need to copy all the files.
        self.__ProtocolFiles.add(protocol_file)
        if force_copy:
            streamProtocol.__ForceCopy = True

        # Pick up the device name of the given serial port: this is actually
        # all we need to bind to it.  The process of binding to the port is a
        # little curious and is system version dependent.
        if Configure.EpicsVersion == '3_13':
            # The older stream device talks directly to the serial port, but
            # requires the name to be hacked: we convert a device name of the
            # form /ty/nn/mm into ty_nn_mm.
            self.port = port.DeviceName()[1:].replace('/', '_')
        else:
            # The new stream device requires that the stream be wrapped as an
            # asyn device.  We do that wrapping here.
            self.port = AsynSerial(port).DeviceName()
            

        # Pick up the protocol name from the file name.
        self.ProtocolName = os.path.basename(protocol_file)

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


    def InitialiseOnce(self):
        # Figure out whether we need to copy the files.  If any protocol
        # needs to be copied or if we are trying to use more than one
        # protocol directory then copying is needed.
        protocol_dirs = set(
            [os.path.dirname(file) for file in self.__ProtocolFiles])
        if self.__ForceCopy or len(protocol_dirs) > 1:
            protocol_dir = 'data'
            for file in self.__ProtocolFiles:
                # Grab a copy of each data file.
                IocDataFile(file)
        else:
            protocol_dir = protocol_dirs.pop()
        print 'STREAM_PROTOCOL_DIR = "%s"' % protocol_dir

        # Reset the global state in case we're reused.
        self.__ProtocolFiles.clear()
        streamProtocol.__ForceCopy = False
        

    def Initialise__3_13(self):
        print '%s_streamBus = "Tty"' % self.port
