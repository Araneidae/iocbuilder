'''Support for hardware devices.  A device is supported in three ways:
    1. when a device is used its supporting library must be loaded into
       the IOC;
    2. when a device is used the device itself must be initialised;
    3. devices may add record definitions, thus extending either the
       set of possible DTYP values or even the set of possible records.
All such entries in the startup script should be implemented by subclassing
the Device class defined here.'''

import os.path

from liblist import Hardware
from libversion import ModuleBase
from dbd import LoadDbdFile
from configure import Configure, Architecture
from support import Singleton


# Here's what this module exports to the outside world
__all__ = ['Device', 'RecordFactory']



# Wrapper routines for local paths to library, object and dbd files.
def _LibPath(file):
    if Configure.dynamic_load:
        return os.path.join('bin', Architecture(), file)
    else:
        return os.path.join('lib', Architecture(), 'lib%s.a' % file)

def _BinPath(file):
    return os.path.join('bin', Architecture(), file)

def _DbdPath(file):
    return os.path.join('dbd', '%s.dbd' % file)


class _FIRST:
    def __hash__(self):     return id(self)
    def __cmp__(self, other):
        if self is other:
            return 0
        else:
            return -1


class Device(ModuleBase):
    '''This class should be subclassed to implement devices.  Each instance of
    this class will automatically announce itself as a device to be
    initialised during IOC startup.

    Each subclass may define the following: each of these methods or
    attributes has appropriate default behaviour, so can be left undefined if
    not needed.

        Dependencies
            A list of modules on which this device depends; may be left
            undefined if there are no dependencies.  

        LibFileList
            The list of library files that need to be loaded for the proper
            operation of this device.

        BinFileList
            Any library binary files that need to be statically loaded.  These
            will be loaded after all the files listed in LibFileList.

        DbdFileList
            The list of DBD files to be loaded for the operation of this
            device.

        InitialiseOnce()
            If defined, this method is called once on the first instance of
            this device to perform any device specific pre-initialisation
            required.

        Initialise()
            This method initialises all the hardware associated with each
            instance of this device

        PostIocInitialise()
            This method performs any initialisation that is required after
            iocInit has been called.

    '''

    BaseClass = True

    FIRST = _FIRST()

    def __init__(self):
        '''Constructing a Device subclass instance adds the class to the list
        of libraries to be loaded and the instance to the list of devices to
        be initialised.'''
        self.__super.__init__()
        
        # Add this instance to the list of devices to be configured
        Hardware.AddHardware(self)

        # Support for commands specified during initialisation.
        self.__Commands = []
        self.__CommandsPostInit = []


    # List of libraries to be loaded as part of the initialisation or
    # preconditions of this device.  This should be overridden by subclasses.
    LibFileList = []
    # List of sys libraries
    SysLibFileList = []
    # List of DBD files to be loaded for this device.  This should be
    # overridden by subclasses.
    DbdFileList = []
    # List of binary files to be loaded dynamically.
    BinFileList = []

    # Default empty definitions for initialisation.
    Initialise = None
    InitialiseOnce = None
    PostIocInitialise = None

    # Initialisation phase: controls when initialisation will occur.
    InitialisationPhase = 0

    
    # This routine generates all the library instance loading code and is
    # called from Hardware during creation of the st.cmd file.  In dynamic
    # mode the library and dbd files are loaded, but in static mode all we do
    # is load the binary files.  
    @classmethod
    def LoadLibraries(cls):
        cls.__Once = False
        
        if cls.BinFileList or Configure.dynamic_load and (
                cls.LibFileList or cls.DbdFileList):
            print
            print '# %s' % cls.__name__
            print 'cd "%s"' % cls.LibPath()
            for file in cls.BinFileList:
                print 'ld < %s' % _BinPath(file)
            if Configure.dynamic_load:
                cls.__LoadDynamicFiles()

    @classmethod
    def __LoadDynamicFiles(cls):
        # This method is only called if dynamic loading is configured.
        for lib in cls.LibFileList:
            print 'ld < %s' % _LibPath(lib)
        if cls.DbdFileList:
            print 'cd "dbd"'
            for dbd in cls.DbdFileList:
                print 'dbLoadDatabase "%s.dbd"' % dbd
                if Configure.register_dbd:
                    print '%s_registerRecordDeviceDriver pdbbase' % dbd
        

    # Calls the initialisation method if present.
    def CallInitialise(self):
        if (self.InitialiseOnce and not self.__Once) or \
                self.Initialise or self.__Commands:
            print
        if self.InitialiseOnce and not self.__Once:
            self.InitialiseOnce()
            self.__class__.__Once = True
        if self.Initialise:
            self.Initialise()
        for command in self.__Commands:
            print command

    # Similarly, call any post-iocInit initialisation
    def CallPostIocInitialise(self):
        if self.PostIocInitialise or self.__CommandsPostInit:
            print
        if self.PostIocInitialise:
            self.PostIocInitialise()
        for command in self.__CommandsPostInit:
            print command


    def AddCommand(self, command, post_init=False):
        if post_init:
            self.__CommandsPostInit.append(command)
        else:
            self.__Commands.append(command)
                

    # This routine is called immediately before the first instance of cls is
    # created.  We add ourselves to the library and load our resources.
    @classmethod
    def UseModule(cls):
        super(Device, cls).UseModule()

        # Add to list of libraries, check that all our resources exist, and
        # finally load the dbd files.
        Hardware.AddLibrary(cls)
        cls.__CheckResources()
        cls.__LoadDbdFiles()


    # Checks all the resources associated with this device
    @classmethod
    def __CheckResources(cls):
        for entity, fileList, makePath in (
                ('library', cls.LibFileList, _LibPath),
                ('object',  cls.BinFileList, _BinPath),
                ('dbd',     cls.DbdFileList, _DbdPath)):
            for fileName in fileList:
                filePath = os.path.join(cls.LibPath(), makePath(fileName))
                assert os.access(filePath, os.R_OK), \
                    'Can\'t find %s file "%s"' % (entity, filePath)

                
    # Informs the DBD layer of the presence of this library and any new
    # record definitions that may now be available.
    @classmethod
    def __LoadDbdFiles(cls):
        for dbd in cls.DbdFileList:
            LoadDbdFile(os.path.join(cls.LibPath(), 'dbd'), '%s.dbd' % dbd)


    # Each device can allocate any interrupt vectors it needs by asking the
    # current hardware instance.
    @classmethod
    def AllocateIntVector(cls, count=1):
        '''This routine allocates a unique interrupt vector on each call.
        This should be used for device initialisation code.  If called with
        count > 0 then a contiguous block of that many interrupt vectors is
        allocated.'''
        return Hardware.AllocateIntVector(count)



class RecordFactory:
    '''This class encapsulates the construction of records from hardware.
    Typically the hardware specific part consists simply of the DTYP
    specification and an address field, which may be computed using extra
    arguments and fields passed to the constructor.'''

    def __init__(self, factory, device, link, address, post=None):
        '''Each record factory is passed a record constructor (factory),
        a link to the associated Device instance (device), the name of the
        EPICS device link (typically 'INP' or 'OUT'), an address string or
        address constructor, and a option addressing fixup routine (post).'''
        self.factory = factory
        self.device = device
        self.link = link
        self.address = address
        self.post = post

    def __call__(self, name, *address_extra, **fields):
        '''Calling a record factory instance builds a record with the given
        name and fields bound to the originating hardware.'''
        
        # If the address is callable then we compute the address using the
        # address hook, simultaneously fixing up any fields that only belong
        # to the address computation.  Otherwise we hope it's a static string
        # (or at least knows how to render itself) and use it as is.
        if callable(self.address):
            address = self.address(fields, *address_extra)
        else:
            assert address_extra == (), 'Unused address arguments'
            address = self.address
        # Build the appropriate type of record
        record = self.factory(name, **fields)

        # Bind the hardware to the device
        record.DTYP = self.device
        setattr(record, self.link, address)

        # Finally allow any special purpose fixup work to be done.
        if self.post:
            self.post(record)
        return record

    def FieldInfo(self):
        return self.factory.FieldInfo()
