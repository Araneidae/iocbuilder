'''Support for hardware devices.  A device is supported in three ways:
    1. when a device is used its supporting library must be loaded into
       the IOC;
    2. when a device is used the device itself must be initialised;
    3. devices may add record definitions, thus extending either the
       set of possible DTYP values or even the set of possible records.
All such entries in the startup script should be implemented by subclassing
the Device class defined here.'''

import os.path
import re

from liblist import Hardware
import libversion
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


# A helper object which sorts before all other objects.
class _FIRST:
    def __hash__(self):     return id(self)
    def __cmp__(self, other):
        if self is other:
            return 0
        else:
            return -1
_FIRST = _FIRST()


# A helper class for printing a header just the once.
class _header:
    def __init__(self, header):
        self.header = header
        self.printed = False
    def doprint(self):
        if not self.printed:
            print self.header
            self.printed = True


_ResourceExclusions = {
    'win32-x86': ['library'],
    'none':      ['library', 'object']
}
# Implements a simple filter on resources against architecture: we don't check
# all resources for all architectures.
def _FilterResource(resource):
    excludes = _ResourceExclusions.get(Architecture())
    return excludes and resource in excludes


## This class should be subclassed to implement devices.  Each instance of
# this class will automatically announce itself as a device to be
# initialised during IOC startup.
#
# Each subclass may define the following: each of these methods or
# attributes has appropriate default behaviour, so can be left undefined if
# not needed.
#
# \param Dependencies
#         A list of modules on which this device depends; may be left
#         undefined if there are no dependencies.
#
# \param LibFileList
#         The list of library files that need to be loaded for the proper
#         operation of this device.
#
# \param SysLibFileList
#         The list of system library files that need to be loaded for the proper
#         operation of this device.
#
# \param BinFileList
#         Any library binary files that need to be statically loaded.  These
#         will be loaded after all the files listed in LibFileList.
#
# \param DbdFileList
#         The list of DBD files to be loaded for the operation of this
#         device.
#
# \param MakefileStringList
#         List of text strings to be placed into the makefile.
#         E.g. MakefileStringList = [
# 'BIN_INSTALLS_WIN32 += $(EPICS_BASE)/bin/$(EPICS_HOST_ARCH)/caRepeater.exe']
#         or   MakefileStringList = [
# '%(ioc_name)s_LDFLAGS_WIN32 += /NOD:nafxcwd.lib /NOD:nafxcw.lib']
#
# \param InitialiseOnce()
#         If defined, this method is called once on the first instance of
#         this device to perform any device specific pre-initialisation
#         required.
#
# \param Initialise()
#         This method initialises all the hardware associated with each
#         instance of this device
#
# \param PostIocInitialise()
#         This method performs any initialisation that is required after
#         iocInit has been called.
class Device(libversion.ModuleBase):
    def __init_meta__(cls, subclass):
        # Load the DBD files as soon as the class is declared.  This allows
        # the record definitions to be available even before the class is
        # instantiated.
        cls._LoadDbdFiles()
        # Compute which initialisation phases are present.
        cls._ComputeInitialisePhases()
        # Per class set of flags used to ensure that InitialiseOnce really is
        # called only the once per class.
        cls._OncePhases = set()

    BaseClass = True

    FIRST = _FIRST      # To be withdrawn at first opportunity!

    def __init__(self):
        # Constructing a Device subclass instance adds the class to the list
        # of libraries to be loaded and the instance to the list of devices to
        # be initialised.
        self.__super.__init__()

        # Add this instance to the list of devices to be configured
        Hardware.AddHardware(self)

        # Support for commands specified during initialisation.
        self.__Commands = []
        self.__CommandsPostInit = []


    ## List of libraries to be loaded as part of the initialisation or
    # preconditions of this device.  This should be overridden by subclasses.
    LibFileList = []
    ## List of sys libraries
    SysLibFileList = []
    ## List of DBD files to be loaded for this device.  This should be
    # overridden by subclasses.
    DbdFileList = []
    ## List of binary files to be loaded dynamically.
    BinFileList = []
    ## List of text strings to go in the makefile
    MakefileStringList = []

    ## Define this method to be called after \c iocInit in the startup script.
    PostIocInitialise = None


    # This routine generates all the library instance loading code and is
    # called from Hardware during creation of the st.cmd file.  In dynamic
    # mode the library and dbd files are loaded, but in static mode all we do
    # is load the binary files.
    @classmethod
    def _LoadLibraries(cls):
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


    # The list of initialisation phases controls when initialisation will occur
    # and is computed automatically from the occurrences of the following
    # Initialise or InitialiseOnce routines:
    #   Initialise__n, InitialiseOnce__n           For phase == -n
    #   Initialise,    InitialiseOnce              For phase == 0
    #   Initialise_n,  InitialiseOnce_n            For phase == n
    # Smaller phases are called before larger phases.
    _MatchInitialise = re.compile('Initialise(Once)?(__?[0-9]+|_FIRST|)$')
    @classmethod
    def _ComputeInitialisePhases(cls):
        # We always include phase 0 because any commands in __Commands are
        # invoked at phase 0.
        phases = set([0])
        for name in dir(cls):
            match = cls._MatchInitialise.match(name)
            if match and match.group(2):
                phase = match.group(2)[1:]
                if phase == 'FIRST':
                    phases.add(_FIRST)
                elif phase[0] == '_':
                    # Negative phase
                    phases.add(-int(phase[1:]))
                else:
                    phases.add(int(phase))
        cls._InitialisationPhases = phases


    # Calls the initialisation methods for the selected phase if present.
    def _CallInitialise(self, phase):
        # The phase suffix is computed from the phase: __n for negative phases,
        # _n for positive phases, empty for (default) phase 0.
        if phase == _FIRST:
            suffix = '_FIRST'
        elif phase < 0:
            suffix = '__%d' % phase
        elif phase > 0:
            suffix = '_%d' % phase
        else:
            suffix = ''
        InitialiseOnce = 'InitialiseOnce%s' % suffix
        Initialise = 'Initialise%s' % suffix

        header = _header('')
        if hasattr(self, InitialiseOnce):
            # An InitialiseOnce for this device at this phase.  Ensure we call
            # this once per class.
            if phase not in self._OncePhases:
                self._OncePhases.add(phase)
                header.doprint()
                getattr(self, InitialiseOnce)()

        if hasattr(self, Initialise):
            header.doprint()
            getattr(self, Initialise)()

        if phase == 0 and self.__Commands:
            header.doprint()
            for command in self.__Commands:
                print command

    # Similarly, call any post-iocInit initialisation
    def _CallPostIocInitialise(self):
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


    # Checks all the resources associated with this device
    @classmethod
    def __CheckResources(cls):
        for entity, fileList, makePath in (
                ('library', cls.LibFileList, _LibPath),
                ('object',  cls.BinFileList, _BinPath),
                ('dbd',     cls.DbdFileList, _DbdPath)):
            for fileName in fileList:
                if not _FilterResource(entity):
                    filePath = os.path.join(cls.LibPath(), makePath(fileName))
                    exists = os.access(filePath, os.R_OK)
                    # .a files only exist if we are doing a static build. If
                    # we are doing a shared build only .so files are created
                    if not exists and entity == 'library' and \
                            filePath.endswith('.a'):
                        exists = os.access(filePath[:-1] + 'so', os.R_OK)
                    assert exists, \
                        'Can\'t find %s file "%s"' % (entity, filePath)


    # Informs the DBD layer of the presence of this library and any new
    # record definitions that may now be available.
    @classmethod
    def _LoadDbdFiles(cls):
        for dbd in cls.DbdFileList:
            LoadDbdFile(cls,
                os.path.join(cls.LibPath(), 'dbd'), '%s.dbd' % dbd)


    ## This routine allocates a unique interrupt vector on each call.  This
    # should be used for device initialisation code.  If called with count > 0
    # then a contiguous block of that many interrupt vectors is allocated.
    @classmethod
    def AllocateIntVector(cls, count=1):
        return Hardware.AllocateIntVector(count)



## This class encapsulates the construction of records from hardware.
# Typically the hardware specific part consists simply of the DTYP
# specification and an address field, which may be computed using extra
# arguments and fields passed to the constructor.
class RecordFactory:

    ## Each record factory is passed a record constructor (factory), a link to
    # the associated Device instance (device), the name of the EPICS device
    # link (typically 'INP' or 'OUT'), an address string or address
    # constructor, and a option addressing fixup routine (post).
    #
    # \param factory
    #   Record constructor to be used.
    # \param device
    #   Associated DTYP setting
    # \param link
    #   Associated address link to go into INP or OUT field.
    # \param address
    #   Field name to receive address link
    # \param post
    #   Optional hook for post processing of fields.
    def __init__(self, factory, device, link, address, post=None):
        self.factory = factory
        self.device = device
        self.link = link
        self.address = address
        self.post = post

    # Calling a record factory instance builds a record with the given name
    # and fields bound to the originating hardware.
    def __call__(self, name, *address_extra, **fields):
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
