# IOC initialisation support.
#
# This file coordinates the initialisation of an IOC: a variety of methods
# are exported from epics for configuring global IOC parameters, and the
# following methods are provided for general use:
#
#   Reset()
#       This is called internally when starting a new IOC and ensures that
#       all values are restored to their defaults. 
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

from support import Singleton
from liblist import Hardware
from libversion import ModuleVersion
import paths



_ExportList = []
def export(function):
    _ExportList.append(function.__name__)
    return function


class iocInit(Singleton):
    DefaultEnvironment = { 'EPICS_TS_MIN_WEST' : 0 }
    
    def __init__(self):
        self.__TargetDir = os.getcwd()
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

    def SetIocName(self, ioc_name):
        self.__IocLib.SetIocName(ioc_name)


    def PrintHeader(self, ioc_root):
        # Print out all the environment settings.  Do this right away before
        # we do anything else, just in case something else we call cares.
        print
        for key, value in self.__EnvList.items():
            print 'putenv "%s=%s"' % (key, value)

        # Set up the working home directory.  If a target directory has
        # been specified then use that.  Otherwise, if __TargetDir is not
        # set then assume that st.cmd will be started in the correct
        # target directory.
        print
        if self.__TargetDir:
            print '# Fixed working directory'
            print 'homeDir = "%s"' % self.__TargetDir
        else:
            # Remember the working directory on entry.
            # The length of homeDir is equal to MAX_FILENAME_LENGTH
            # (Tornado2.2/host/include/host.h) which is equal to
            # _POSIX_PATH_MAX+1.
            print '# Pick up working directory on entry.'
            print 'homeDir = malloc(256)'
            if ioc_root:
                print 'cd "%s"' % ioc_root
            print 'ioDefPathGet(homeDir)'

        # vxWorks and Diamond specific configuration hacks
        print
        print 'tyBackspaceSet(127)'
        if self.__ClockRate:
            print 'sysClkRateSet(%d)' % self.__ClockRate
        if self.__Gateway:
            print 'routeAdd "0", "%s"' % self.__Gateway
        print 


    def PrintFooter(self):
        print
        print '# Final ioc initialisation'
        print '# ------------------------'
        print 'cd homeDir'
        for database in self.__DatabaseNameList:
            print 'dbLoadRecords "%s"' % database

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
    def SetTargetDir(self, targetDir):
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


        
class IocDataFile:
    '''This class is used to package files which need to be copied into the
    IOC.  The target directory is set by the IOC writer,  relative to homeDir;
    the source file is set by the constructor.
    '''

    # Ensure that when this class is used as a database field it isn't
    # validated on assignment: this can be too early for path resolution!
    ValidateLater = True

    # The following global state is managed as class variables.
    __DataPath = None
    __DataFileList = {}

    @classmethod
    def Reset(cls):
        cls.__DataPath = None
        cls.__DataFileList = {}

    @classmethod
    def SetDataPath(cls, DataPath):
        '''Assigns the path to the data directory as seen by the IOC.'''
        cls.__DataPath = DataPath

    @classmethod
    def GetDataPath(cls):
        assert cls.__DataPath is not None, 'IOC data path not yet defined'
        return cls.__DataPath

    @classmethod
    def CopyDataFiles(cls, targetDir):
        assert cls.__DataPath is not None, 'IOC data path not yet defined'
        targetDir = os.path.join(targetDir, cls.__DataPath)
        os.makedirs(targetDir)
        for filename, file_object in cls.__DataFileList.items():
            shutil.copyfile(
                file_object.source, os.path.join(targetDir, filename))

        # Once the data files have been copied our work is done (so long as
        # this is done after database generation!)  Reset our internal state.
        cls.Reset()

    @classmethod
    def DataFileCount(cls):
        return len(cls.__DataFileList)
            

    def __init__(self, source_file):
        _, self.name = os.path.split(source_file)
        self.source = source_file
        assert os.access(self.source, os.R_OK), \
            'File "%s" not readable' % self.source

        try:
            file_entry = self.__DataFileList[self.name]
        except KeyError:
            # New entry: just add ourself to the list of files
            self.__DataFileList[self.name] = self
        else:
            # Existing entry: check that we're actually handling exactly the
            # same underlying file (this is handled by the override of cmp).
            assert self == file_entry, \
                'File %s already added to IOC with different path %s' % (
                    self.source, file_entry.source)

    def Path(self):
        assert self.__DataPath is not None, 'IOC data path not yet defined'
        return os.path.join(self.__DataPath, self.name)

    def __str__(self):
        return self.Path()

    # Hash this object by the full source filename
    def __hash__(self):         return hash(self.source)
    def __cmp__(self, other):   return cmp(self.source, other.source)


    
# Export all the names exported by iocInit()
__all__ = ['IocDataFile']
for name in _ExportList:
    __all__.append(name)
    globals()[name] = getattr(iocInit, name)
