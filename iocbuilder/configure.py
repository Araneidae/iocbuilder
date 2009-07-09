# Epics framework configuration and IOC reset

import os

from support import Singleton


__all__ = [
    'Configure', 'LoadVersionFile', 'ConfigureIOC', 'ConfigureTemplate',
    'Architecture', 'TargetOS']


def Architecture():
    return Configure.architecture

    
def TargetOS():
    '''Returns the target OS for the configured architecture, currently
    either linux or vxWorks.'''
    return Architecture().split('-', 1)[0]

    
def Call_TargetOS(self, name, *args, **kargs):
    '''Helper function for calling a target OS specific function.  Looks up
        self.<name>_<TargetOS()>
    and calls it with the given arguments if found, otherwise returns None.'''
    targetOS = TargetOS()
    try:
        method = getattr(self, '%s_%s' % (name, targetOS))
    except AttributeError:
        return None
    else:
        return method(*args, **kargs)

    
class Configure(Singleton):
    # Ensure we don't have to cope with multiple reconfigurations.
    __called = False

    def __call__(self,
            module_path  = None,
            record_names = None,
            ioc_writer   = None,
            dynamic_load = False,
            architecture = 'none',
            register_dbd = False):

        assert not self.__called, 'Cannot call Configure more than once!'
        self.__called = True

        import paths
        import libversion
        import iocinit
        import recordnames
        import iocwriter

        self.architecture = architecture
        
        # Configure where ModuleVersion looks for modules.
        if module_path is None:
            module_path = paths.module_path
        libversion.SetModulePath(module_path)
        
        # Unfortunately we can't initialise iocinit until the iocbuilder
        # module is complete, in particular this can't be called from within
        # __init__.py.  So now instead.
        iocinit.iocInit.Initialise()

        # Configure core ioc parameters.
        self.dynamic_load = dynamic_load
        self.register_dbd = register_dbd

        # Both recordnames and iocwriter can add names to the global names.
        if record_names is None:
            record_names = recordnames.BasicRecordNames()
        self.__PublishNames(record_names)
        recordnames.RecordNames = record_names

        if ioc_writer is None:
            ioc_writer = iocwriter.SimpleIocWriter()
        self.__PublishNames(ioc_writer)
        

    # Add the names listed in the given configuration object to the set of
    # global names published by the epics library.
    def __PublishNames(self, configuration):
        if hasattr(configuration, '__all__'):
            for name in configuration.__all__:
                self.__add_symbol(name, getattr(configuration, name))


def LoadVersionFile(filename, **context):
    '''Loads a list of module version declarations.  The given file is
    executed with execfile() with the ModuleVersion() function already in
    scope: no other calls or definitions should occur in the file.'''
    from libversion import ModuleVersion
    execfile(filename, dict(context,
        ModuleVersion = ModuleVersion,
        __file__ = filename))


# Some sensible default configurations.

def ConfigureIOC(
        architecture = 'vxWorks-ppc604_long',
        module_path = None):
    import recordnames
    import iocwriter
    Configure(
        module_path  = module_path,
        record_names = recordnames.DiamondRecordNames(),
        ioc_writer   = iocwriter.DiamondIocWriter,
        dynamic_load = False,
        architecture = architecture,
        register_dbd = True)


def ConfigureTemplate(record_names = None):
    import recordnames
    if record_names is None:
        record_names = recordnames.TemplateRecordNames()
    Configure(record_names = record_names)
