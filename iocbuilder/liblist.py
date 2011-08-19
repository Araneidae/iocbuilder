import sys
import os.path

from support import Singleton



# The Hardware class manages the list of libraries to be loaded and hardware
# entities to be initialised.
#
# Each device has both a library which needs to be loaded (once for all
# instances of the device) and instance specific initialisation which is
# most safely done after all the libraries have been loaded: thus we have
# two initialisation lists.

class Hardware(Singleton):
    # Initialises the internal state of this module so that only the built-in
    # library instances are loaded.

    def __init__(self):
        # Each entity on the library list must support the CallLoadLibrary
        # method which should write out the initialisation code required to
        # load this library.  The code generated via this list is executed
        # directly after ioc startup.
        self.__LibraryList = []
        # Each entity on the hardware list should support the Initialise
        # method.  The code generated via this list is executed after the
        # libraries have been loaded but before iocInit is started and
        # databases are loaded.
        self.__HardwareList = []

        # Interrupt vectors are allocated from a safe range determined by the
        # particular vxWorks configuration.
        self.__IntVector = 0xC0


    # The code below follows Pete Owen's algorithm as implemented in
    # support/utility/Rx-y/utilityApp/src/newInterruptVector.c.  This is used
    # to safely allocate interrupt vectors to hardware.
    def AllocateIntVector(self, count=1):
        result = self.__IntVector
        assert result + count <= 255, \
            'No more interrupt vectors left to allocate'
        self.__IntVector += count
        return result


    # This exported method generates a vxWorks startup script containing all of
    # the initialisation code required to start the ioc and all of the records
    # and supporting activities that have been generated.
    #
    # All hardware initialisation code is written out in the form of a
    # vxWorks startup script.  First all of the libraries required by each
    # hardware resource are loaded, and then each hardware device is
    # initialised as appropriate.
    def PrintBody(self):
        # Now load all the dependent libraries
        print
        print '# Loading libraries'
        print '# -----------------'
        for l in self.__LibraryList:
            # Generate the code to load the library.
            l._LoadLibraries()

        # Now write the individual device initialisations.
        # Initialisation is normally done in order of creation, but an
        # initialisation phase can be configured for delayed initialisation.
        print
        print '# Device initialisation'
        print '# ---------------------'
        device_phases = {}
        for device in self.__HardwareList:
            for phase in device._InitialisationPhases:
                device_phases.setdefault(phase, []).append(device)

        for phase in sorted(device_phases.keys()):
            for device in device_phases[phase]:
                device._CallInitialise(phase)


    # Returns a list of all .dbd files.
    def GetDbdList(self):
        return [dbd
            for library in self.__LibraryList
            for dbd in library.DbdFileList]

    # Returns a list of all library files.
    def GetLibList(self):
        return [lib
            for library in self.__LibraryList
            for lib in library.LibFileList]

    # Returns a list of all system library files.
    def GetSysLibList(self):
        return [lib
            for library in self.__LibraryList
            for lib in library.SysLibFileList]

    # Returns a list of all system library files.
    def GetMakefileStringList(self):
        return [text
            for library in self.__LibraryList
            for text in library.MakefileStringList]

    # Any devices which need post iocInit() initialisation can have their
    # code generation here
    def PrintPostIocInit(self):
        for device in self.__HardwareList:
            device._CallPostIocInitialise()


    # Add device library to list of libraries to be loaded.  Called from
    # Device class, which will be responsible for initialising it.
    def AddLibrary(self, library):
        assert library not in self.__LibraryList
        self.__LibraryList.append(library)

    # Add device instance to list of hardware to be initialised.
    def AddHardware(self, device):
        self.__HardwareList.append(device)
