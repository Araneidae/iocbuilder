# Epics framework configuration and IOC reset

import os

from support import Singleton

# Note that the configure module must not import any symbols directly from
# any of the modules below: this rule is necessary to avoid import dependency
# loops.
import recordset, recordbase, dbd
import iocinit, liblist, libversion


__all__ = ['Configure']


def ResetIoc():
    '''Called back from the IocCmd.Reset() method to complete any final
    resetting required.  Also called each time Configure() is called to
    ensure that everything is reinitialised.'''

    if Configure.recordnames:
        Configure.recordnames.Reset()
    recordset.Reset()   # Redundant?

    dbd.Reset()
    liblist.Hardware.Reset()
    if Configure.baselib:
        iocinit.iocInit.Reset(Configure.baselib)


    
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

    # Support nested calling of Configure: only call ResetIoc on exit from
    # the outermost call.
    __NestedCallDepth = 0


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

        self.__NestedCallDepth += 1

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
            # Withdraw any global names publshed by any earlier version of
            # this entity.
            self.__WithdrawNames(key)
            # Retain the new configuration entity into the framework state.
            setattr(self, key, value)
            # If any particular configuration is required, do it now.
            if configure:
                configure(self)
            # Finally publish the names provided by this entity.
            self.__PublishNames(key)

        self.__NestedCallDepth -= 1
        if self.__NestedCallDepth == 0:
            # Ensure that everything is in a consistent initial state after
            # this has been called.
            ResetIoc()
        

    # Add the names listed in the given configuration object to the set of
    # global names published by the epics library.
    def __PublishNames(self, config_name):
        configuration = getattr(self, config_name)
        if hasattr(configuration, '__all__'):
            for name in configuration.__all__:
                self.__add_symbol(name, getattr(configuration, name))

                
    # Remove the names listed in an old configuration object from the set of
    # published global names.
    def __WithdrawNames(self, config_name):
        configuration = getattr(self, config_name)
        if hasattr(configuration, '__all__'):
            for name in configuration.__all__:
                self.__delete_symbol(name)
            

    # Configuration specific initialisation.

    def __ConfigureRecordNames(self):
        recordbase.BindNames(self.recordnames)

    def __ConfigureVersion(self):
        self.EpicsVersion = self.version
        
        libversion.ResetModuleVersions()
        execfile(os.path.join(os.path.dirname(__file__),
            'versions_%s.py' % self.EpicsVersion), self.__globals())


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
        'baselib'      : None,
        'dynamic_load' : None,
        'architecture' : None,
        'register_dbd' : None }
