# IOC initialisation support.
#
# This file coordinates the initialisation of an IOC: a variety of methods
# are exported from epics for configuring global IOC parameters, and the
# following methods are provided for general use:
#
#   PrintHeader()
#       Prints the preamble of an IOC initialisation file, including most of
#       the IOC configuration settings defined by the Set... functions.
#
#   PrintFooter()
#       Prints the postamble to the IOC initialisation, including the code
#       required to load the configured database files.
#
# Supports the following configurations:
#
#   AddDatabaseName(database)
#       Called (indirectly) from the IOC writer: adds the named database to
#       the startup script.
#
#   EpicsEnvSet(key, value)
#       Adds key=value to startup script.
#
#   AddIocFile(filename)
#       Adds file to be copied into IOC directory tree.

import os
import shutil

from support import Singleton, autosuper_object, quote_c_string
from liblist import Hardware
from libversion import ModuleVersion
from configure import TargetOS, Call_TargetOS
import paths



_ExportList = []
def export(function):
    _ExportList.append(function.__name__)
    return function


def quote_IOC_string_none(text):
    assert False, 'Architecture not specified'

_safe_chars = set([ord('\t')]) | set(range(ord(' '), 128))
def quote_IOC_string_linux(text):
    # Quoting in the linux EPICS IOC shell is a complete mess.  No
    # non-printing characters are supported, as there is no quotation
    # mechanism, and quote characters need to be handled specially anyway!
    text = str(text)
    unsafe_chars = set(map(ord, text)) - _safe_chars
    assert not unsafe_chars, \
        'Unquotable characters %s in message' % unsafe_chars
    quote = '\''
    return quote + '\'"\'"\''.join(text.split(quote)) + quote
    

quote_IOC_string_vxWorks = quote_c_string


class iocInit(Singleton):
    DefaultEnvironment = { 'EPICS_TS_MIN_WEST' : 0 }
    
    def __init__(self):
        self.__TargetDir = None
        self.__Gateway = None
        self.__ClockRate = None
        
        # List of databases to be loaded into this ioc
        self.__DatabaseNameList = []
        self.__EnvList = dict(self.DefaultEnvironment)

        # Extra commands (for bypassing device creation)
        self.__IocCommands_PreInit = []
        self.__IocCommands_PostInit = []

        
    def Initialise(self):
        # We can't import the IOC until we've finished importing (at least,
        # not if we want EPICS_BASE to behave like other modules), so we have
        # to put off creating it until configure tells us to initialise.
        ModuleVersion('EPICS_BASE', home = paths.EPICS_BASE, use_name = False)
        from modules.EPICS_BASE import epicsBase
        self.__IocLib = epicsBase()

        # Now the architecture has been set (assuming it has), set up the
        # appropriate IOC string quoting function.
        global quote_IOC_string
        quote_IOC_string = globals().get(
            'quote_IOC_string_%s' % TargetOS(), quote_IOC_string_none)

    def SetIocName(self, ioc_name):
        self.__IocLib.SetIocName(ioc_name)


    def PrintHeader_vxWorks(self, ioc_root):
        # Set up the working home directory.  If a target directory has
        # been specified then use that.  Otherwise, if __TargetDir is not
        # set then assume that st.cmd will be started in the correct
        # target directory.
        if self.__TargetDir is None:
            # Remember the working directory on entry.
            # The length of HOME_DIR is equal to MAX_FILENAME_LENGTH
            # (Tornado2.2/host/include/host.h) which is equal to
            # _POSIX_PATH_MAX+1.
            print '# Pick up working directory on entry.'
            print 'HOME_DIR = malloc(256)'
            if ioc_root:
                print 'cd %s' % quote_IOC_string(ioc_root)
            print 'ioDefPathGet(HOME_DIR)'
        print
        print 'tyBackspaceSet(127)'

        
    def cd_home_vxWorks(self):
        print 'cd HOME_DIR'
    def cd_home_linux(self):
        print 'cd "${HOME_DIR}"'
    def cd_home(self):
        if self.__TargetDir:
            print 'cd %s' % quote_IOC_string(self.__TargetDir)
        else:
            Call_TargetOS(self, 'cd_home')


    def PrintHeader(self, ioc_root):
        # Print out all the environment settings.  Do this right away before
        # we do anything else, just in case something else we call cares.
        print
        for key, value in self.__EnvList.items():
            print 'epicsEnvSet "%s", %s' % (key, quote_IOC_string(value))

        print
        Call_TargetOS(self, 'PrintHeader', ioc_root)
        if self.__ClockRate:
            print 'sysClkRateSet %d' % self.__ClockRate
        if self.__Gateway:
            print 'routeAdd "0", %s' % quote_IOC_string(self.__Gateway)
        print 


    def PrintFooter(self):
        print
        print '# Final ioc initialisation'
        print '# ------------------------'
        self.cd_home()
        for database in self.__DatabaseNameList:
            print 'dbLoadRecords %s' % quote_IOC_string(database)

        if self.__IocCommands_PreInit:
            print
            print '# Extra IOC commands'
            for command in self.__IocCommands_PreInit:
                print command
            print

        print 'iocInit'

        if self.__IocCommands_PostInit:
            print
            print '# Extra post-init IOC commands'
            for command in self.__IocCommands_PostInit:
                print command
            print

        
    def PrintIoc(self, ioc_root=None):
        '''Writes out a complete IOC startup script.'''
        self.PrintHeader(ioc_root)
        Hardware.PrintBody()
        self.PrintFooter()
        Hardware.PrintPostIocInit()

        

    def AddDatabaseName(self, database):
        self.__DatabaseNameList.append(database)

        
    @export
    def SetTargetDir(self, targetDir=None):
        '''Sets the working directory for the IOC.  This path will be assigned
        to the homeDir environment variable, and all other IOC files will be
        loaded relative to this directory.
            If targetDir=None is passed then instead the working directory on
        startup will be picked up as homeDir.  This is preferable, if possible,
        as it allows the IOC to be relocated.'''
        self.__TargetDir = targetDir

    @export
    def SetEpicsPort(self, EpicsPort):
        '''Sets the server and repeater ports to be used for EPICS
        communication.  The default port of 5064 does not need to be set.'''
        self.EpicsEnvSet('EPICS_CA_SERVER_PORT', EpicsPort)
        self.EpicsEnvSet('EPICS_CA_REPEATER_PORT', EpicsPort + 1)

    @export
    def SetGateway(self, Gateway):
        '''Sets the IP address of the network gateway.'''
        self.__Gateway = Gateway

    @export
    def SetNtpServer(self, NtpServer):
        '''Sets the IP address of the NTP server to be used.'''
        self.EpicsEnvSet('EPICS_TS_NTP_INET', NtpServer)

    @export
    def SetEpicsLogging(self, LogAddress, LogPort):
        '''Sets machine IP address and port for EPICS logging.'''
        self.EpicsEnvSet('EPICS_IOC_LOG_INET', LogAddress)
        self.EpicsEnvSet('EPICS_IOC_LOG_PORT', LogPort)

    @export
    def SetClockRate(self, ClockRate):
        '''Sets the IOC clock rate.  The default clock rate is 60Hz, and
        changing this can cause some drivers to stop working.'''
        self.__ClockRate = ClockRate

    @export
    def EpicsEnvSet(self, key, value):
        '''Adds a key=value setting to the startup script.'''
        if key in self.__EnvList and value != self.__EnvList[key]:
            print 'Changing environment variable %s from %s to %s' % (
                key, self.__EnvList[key], value)
        self.__EnvList[key] = value

    @export
    def IocCommand(self, command, post_init=False):
        if post_init:
            self.__IocCommands_PostInit.append(command)
        else:
            self.__IocCommands_PreInit.append(command)


        
class IocDataSet(Singleton):
    '''This class gathers together files to be placed in the IOC's data
    directory.'''
    
    # The following global state is managed as class variables.
    __DataPath = None
    __DataFileList = {}

    def SetDataPath(self, DataPath):
        '''Assigns the path to the data directory as seen by the IOC.'''
        self.__DataPath = DataPath

    def GetDataPath(self):
        assert self.__DataPath is not None, 'IOC data path not yet defined'
        return self.__DataPath

    def CopyDataFiles(self, targetDir):
        assert self.__DataPath is not None, 'IOC data path not yet defined'
        targetDir = os.path.join(targetDir, self.__DataPath)
        os.makedirs(targetDir)
        for filename, file_object in self.__DataFileList.items():
            file_object._CopyFile(os.path.join(targetDir, filename))

    def DataFileCount(self):
        return len(self.__DataFileList)

    def _AddDataFile(self, file_object, name):
        try:
            file_entry = self.__DataFileList[name]
        except KeyError:
            # New entry: just add ourself to the list of files
            self.__DataFileList[name] = file_object
        else:
            # Existing entry: check that we're actually handling exactly the
            # same underlying file (this is handled by the override of cmp).
            assert file_object == file_entry, \
                'File %s already added to IOC with different path' % name


class _IocDataBase(autosuper_object):
    # Ensure that when this class is used as a database field it isn't
    # validated on assignment: this can be too early for path resolution!
    ValidateLater = True

    # A convenient alias.
    GetDataPath = IocDataSet.GetDataPath
                
    def __init__(self, name):
        self.name = name
        IocDataSet._AddDataFile(self, name)

    def Path(self):
        return os.path.join(IocDataSet.GetDataPath(), self.name)

    def __str__(self):
        return self.Path()



class IocDataFile(_IocDataBase):
    '''This class is used to package files which need to be copied into the
    IOC.  The target directory is set by the IOC writer,  relative to homeDir;
    the source file is set by the constructor.
    '''

    def __init__(self, source_file):
        source_file = os.path.abspath(source_file)
        _, name = os.path.split(source_file)
        self.source = source_file
        assert os.access(source_file, os.R_OK), \
            'File "%s" not readable' % source_file

        self.__super.__init__(name)

    def _CopyFile(self, filename):
        shutil.copyfile(self.source, filename)

    # Treat two instances wrapping the same file as equal.
    def __cmp__(self, other):   return cmp(self.source, other.source)


class IocDataStream(_IocDataBase):
    '''This is used to package up a data stream which will be written to a
    freshly generated file at the end of the IOC build process.'''

    def __init__(self, name, mode=None):
        self.content = []
        self.__super.__init__(name)
        self.written = False
        self.mode = mode

    def write(self, text):
        assert not self.written, \
            'Content of %s already written out' % self.name
        self.content.append(text)

    def _CopyFile(self, filename):
        output = file(filename, 'w')
        for content in self.content:
            if callable(content):
                content = content()
            output.write(content)
        output.close()
        if self.mode is not None:
            os.chmod(filename, self.mode)
        self.written = True

    
# Export all the names exported by iocInit()
__all__ = ['IocDataFile', 'IocDataStream']
for name in _ExportList:
    __all__.append(name)
    globals()[name] = getattr(iocInit, name)