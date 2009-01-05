# Epics framework configuration and IOC reset

import os

from support import Singleton, SameDirFile



__all__ = ['Configure', 'LoadVersionFile', 'ConfigureVmeIOC']

    
class Configure(Singleton):
    '''Manages the global configuration of the epics builder framework.
    Extensions to the frameworks should be managed via this class.'''

    # Placeholders for configurations.
    recordnames  = None
    iocwriter    = None
    version      = None
    baselib      = None
    architecture = None
    dynamic_load = True
    register_dbd = False

    # Ensure we don't have to cope with multiple reconfigurations.
    __called = False


    def __call__(self, **configurations):
        '''Set up configuration options for the epics library.  Calls to
        configure should be completed before any other work is done, as the
        library is normally reinitialised after reconfiguration.

        The following configurations can be set:
        
        -    recordnames=RecordNameInstance
             The RecordNameInstance must support the following methods:
             -   fullname = RecordName(name)
                 This will be called to compute the true record name each
                 time a record is created.
             -   Reset()
                 This will be called each time the set of records has been
                 written out to reset any record name state.
        -    iocwriter=IocWriterInstance
        -    version='version string'

        Each configuration entity can also define a list of names which will
        be added to the list of names exported by the epics library.'''

        assert not self.__called, 'Cannot call Configure more than once!'
        self.__called = True

        # The generic configuration process is straightforward and uniform.
        # Every configuration is retained within the framework as a single
        # named entity.  This entity may publish a number of module global
        # names, and may require entity specific configuration initialisation.
        for key, value in configurations.items():
            assert key in self.__Configure, \
                'Invalid configuration option "%s"' % key
            # Check that this configuration name is valid and pick up any
            # specific configuration.
            configure = self.__Configure[key]
            # Retain the new configuration entity into the framework state.
            setattr(self, key, value)
            # If any particular configuration is required, do it now.
            if configure:
                configure(self)
            # Finally publish the names provided by this entity.
            self.__PublishNames(key)
        

    # Add the names listed in the given configuration object to the set of
    # global names published by the epics library.
    def __PublishNames(self, config_name):
        configuration = getattr(self, config_name)
        if hasattr(configuration, '__all__'):
            for name in configuration.__all__:
                self.__add_symbol(name, getattr(configuration, name))


    # Configuration specific initialisation.

    def __ConfigureRecordNames(self):
        import recordnames
        recordnames.RecordNames = self.recordnames

    def __ConfigureVersion(self):
        self.EpicsVersion = self.version

    def __ConfigureBaselib(self):
        import iocinit
        iocinit.iocInit.SetInitialLibrary(self.baselib)
        

    def LoadVersionFile(self, filename):
        '''Loads a list of module version declarations.  The given file is
        executed with execfile() with the ModuleVersion() function already
        in scope: no other calls or definitions should occur in the file.
        '''
        ModuleVersion = self.__globals()['ModuleVersion']
        execfile(filename, dict(ModuleVersion = ModuleVersion))


    # List of allowable configuration settings and any configuration actions.
    __Configure = {
        'recordnames'  : __ConfigureRecordNames,
        'iocwriter'    : None,
        'version'      : __ConfigureVersion,
        'baselib'      : __ConfigureBaselib,
        'dynamic_load' : None,
        'architecture' : None,
        'register_dbd' : None }


# Some sensible default configurations.

def ConfigureVmeIOC(module_path = '/dls_sw/prod/R3.14.8.2/support'):
    import libversion
    import recordnames
    import iocwriter
    from hardware import baselib
    
    libversion.SetModulePath(module_path)
    libversion.ModuleVersion('EPICS_BASE',
        home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)
    Configure(
        baselib = baselib.epicsBase,
        dynamic_load = False,
        register_dbd = True,
        architecture = 'vxWorks-ppc604_long',
        recordnames = recordnames.DiamondRecordNames(),
        iocwriter = iocwriter.DiamondIocWriter,
        version = '3_14')


LoadVersionFile = Configure.LoadVersionFile
