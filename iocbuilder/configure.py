# Epics framework configuration and IOC reset

import os

import paths
from support import Singleton, SameDirFile


__all__ = [
    'Configure', 'LoadVersionFile', 'ConfigureIOC', 'ConfigureTemplate']

    
class Configure(Singleton):
    '''Manages the global configuration of the epics builder framework.
    Extensions to the frameworks should be managed via this class.'''

    # Placeholders for configurations.
    recordnames  = None
    iocwriter    = None
    dynamic_load = True
    architecture = None
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



    # List of allowable configuration settings and any configuration actions.
    __Configure = {
        'recordnames'  : __ConfigureRecordNames,
        'iocwriter'    : None,
        'dynamic_load' : None,
        'architecture' : None,
        'register_dbd' : None }


def LoadVersionFile(filename):
    '''Loads a list of module version declarations.  The given file is
    executed with execfile() with the ModuleVersion() function already in
    scope: no other calls or definitions should occur in the file.'''
    from libversion import ModuleVersion
    execfile(filename, dict(
        ModuleVersion = ModuleVersion,
        __file__ = filename))


# Some sensible default configurations.

def ConfigureIOC(
        architecture = 'vxWorks-ppc604_long',
        module_path = paths.module_path):
    import libversion
    import recordnames
    import iocwriter
    import iocinit

    libversion.SetModulePath(module_path)
    iocinit.iocInit.Initialise()
    Configure(
        dynamic_load = False,
        register_dbd = True,
        architecture = architecture,
        recordnames = recordnames.DiamondRecordNames(),
        iocwriter = iocwriter.DiamondIocWriter)


def ConfigureTemplate(record_names = None):
    import libversion
    import recordnames
    import iocwriter
    import iocinit
    
    if record_names is None:
        record_names = recordnames.TemplateRecordNames()
    libversion.SetModulePath(None)
    iocinit.iocInit.Initialise()
    Configure(
        recordnames = record_names, 
        iocwriter = iocwriter.SimpleIocWriter())
