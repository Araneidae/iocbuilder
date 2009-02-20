#   Generic hardware module support

import sys
import os
import string
import re
from types import ModuleType

from support import autosuper_meta, SameDirFile, CreateModule
from configure import Configure

import hardware


__all__ = [
    'ModuleVersion', 'ModuleBase', 'modules',
    'autodepends', 'annotate_args']




def SetModulePath(prod):
    '''Define the directory path for locating modules.  This works with the
    Diamond directory conventions.'''
    global prodSupport
    prodSupport = prod


def _CheckPythonModule(path, module):
    # Checks for a Python module or package at path/module, returns the path
    # to the python path to execute and a flag indicating whether the file is
    # a package.
    Places = [
        # Follow Python by first trying for a package before a plain module.
        (os.path.join(path, module, '__init__.py'), True),
        (os.path.join(path, '%s.py' % module),      False)]
    for ModuleFile, IsPackage in Places:
        if os.access(ModuleFile, os.R_OK):
            return (ModuleFile, IsPackage)
    else:
        return (None, False)


_ValidNameChars = re.compile(
    '[^' + 
    string.ascii_uppercase + string.ascii_lowercase +
    string.digits + '_' + ']')

def PythonIdentifier(name):
    '''Converts an arbitrary string into a valid Python identifier.'''

    name = _ValidNameChars.sub('_', name)
    if len(name) == 0 or name[0] in set(string.digits):
        name = '_' + name
    return name

    


# Module version information specifying:
#   name     Directory name of module
#   version  Version of module
#   home     Home directory to locate module
class ModuleVersion:
    '''Create instances of this class to declare the version of each module
    to be used.'''

    # Set of module macro names already allocated, used to ensure no clashes.
    __MacroNames = set()

    # This is set while the module is being loaded so that we can detect
    # nested loads (really bad idea) and can treat the module name specially
    # in ModuleBase.
    _LoadingModule = None
    
    def __init__(self, libname,
            version=None, home=None, use_name=True,
            suppress_import=False, load_path=None, override=False):
        if home is None:
            # By default pick up each module from the prod support directory.
            # It might be quite nice to extend this with a path search.
            home = prodSupport
        else:
            # Normalise the path for safety.
            home = os.path.realpath(home)

        self.__name = libname
        self.__module_name = PythonIdentifier(libname)
        self.version = version
        self.home = home
        self.use_name = use_name

        self.__macroname = libname.upper()
        assert self.__macroname not in self.__MacroNames, \
            'Module with macro name %s already defined' % self.__macroname
        self.__MacroNames.add(self.__macroname)

        # A couple of sanity checks: libname must not be already defined iff
        # version override has not been requested.
        libDefined = libname in _ModuleVersionTable
        assert (not override) <= (not libDefined), \
               'Module %s multiply defined' % libname
        assert override <= libDefined, 'Module %s not defined' % libname
        
        # Add this to the list of module versions, create the associated
        # module and finally attempt to load any definitions associated with
        # this module.
        _ModuleVersionTable[libname] = self
        self.__CreateVersionModule()
        if suppress_import:
            print 'Import of %s skipped' % self.__name
        else:
            self.__LoadModuleDefinitions(load_path)
        

    def LibPath(self, macro_name=False):
        '''Returns the path to the module directory defined by this entry.
        If macro_name is set then a form suitable for macro expansion is
        returned.'''
        if macro_name:
            return '$(%s)' % self.__macroname
        
        path = self.home
        if self.use_name:
            path = os.path.join(path, self.__name)
        if self.version:
            path = os.path.join(path, self.version)
        return path

    def ModuleFile(self, filename):
        '''Returns an absolute path to a file within this module.'''
        filename = os.path.join(self.LibPath(), filename)
        assert os.access(filename, os.R_OK), 'File "%s" not found' % filename
        return filename

    def Name(self):
        '''Returns the EPICS module name.'''
        return self.__name

    def MacroName(self):
        return self.__macroname

    def ModuleName(self):
        '''Returns the Python identifier naming this module.  This is the
        EPICS module name converted to a valid Python identifier.'''
        return self.__module_name

    # The following definitions ensure that when hashed and when compared
    # this class behaves exactly like its name: this ensures that sets and
    # sorted lists of modules behave predicably.
    def __hash__(self):         return hash(self.__name)
    def __cmp__(self, other):   return cmp(self.__name, other.__name)


    def __CreateVersionModule(self):
        # Create the associated module and record it in our list of loaded
        # modules.  If we can find any module definitions then they will be
        # loaded into this module.
        ModuleName = 'iocbuilder.modules.%s' % self.__module_name
        self.module = CreateModule(ModuleName)
        setattr(modules, self.__module_name, self.module)
        self.ClassesList = []
        modules.LoadedModules[self.__module_name] = self.ClassesList

        # Create some useful module properties.
        self.module.ModuleVersion = self
        self.module.LibPath = self.LibPath
        self.module.ModuleFile = self.ModuleFile


    def __LoadModuleDefinitions(self, load_path):
        if load_path:
            ModuleFile, IsPackage = _CheckPythonModule(load_path, self.__name)
        else:
            Places = [
                # First look for a builder package in the loaded EPICS module
                (self.LibPath(), 'builder'),
                # Failing that, try for a defaults entry.
                (SameDirFile(__file__, 'defaults'), self.__name)]
            for path, module in Places:
                ModuleFile, IsPackage = _CheckPythonModule(path, module)
                if ModuleFile:
                    break

        if ModuleFile:
            ModuleFile = os.path.abspath(ModuleFile)
            self.module.__file__ = ModuleFile
            if IsPackage:
                # Convert the module into a package by setting up the file
                # name and path so that it looks like a convincing Python
                # package.  Now executing execfile has the desired effect of
                # ensuring that all imports with ModuleFile are treated as
                # local to ModuleFile.
                self.module.__path__ = [os.path.dirname(ModuleFile)]
            
            assert self._LoadingModule is None, \
                'Calling ModuleVersion inside an EPICS module is a BAD idea!'
            ModuleVersion._LoadingModule = self
            execfile(ModuleFile, self.module.__dict__)
            ModuleVersion._LoadingModule = None
            
            if hasattr(self.module, '__all__'):
                for name in self.module.__all__:
                    assert not hasattr(hardware, name), \
                        'Value %s.%s already in hardware module' % (
                            self.__name, name)
                    setattr(hardware, name, getattr(self.module, name))
        else:
            print 'Module definitions for', self.__name, 'not found'

    

class ModuleBase(object):
    '''All entities which need to depend on module versions should subclass
    this class to obtain access to their configuration information.

    By default the name of the class will be used both as an index into the
    ModuleVersion entry and as the subdirectory name in the support directory.
    When the external name of the module doesn't match the class name then
    the symbol ModuleName should be set equal to the external module name
    thus:
        ModuleName = 'true-module-name'

    This class will always define a ModuleName symbol.  If the same module
    is to be used by all subclasses then this can be enabled by defining the
    symbol
        InheritModuleName = True
    '''

    # Meta class used for module instances: ensures that the ModuleName
    # symbol exists, defaulting to the class name.
    # 
    # Optionally the ModuleName can be inherited from the base class if the
    # symbol InheritModuleName is set to True.
    class __ModuleBaseMeta(autosuper_meta):
        def __init__(cls, name, bases, dict):
            # This could more simply be written as autosuper_meta.__..., but
            # then subclassing might go astray.  Module instances are already
            # heavily subclassed, so we ought to play by the rules.
            super(cls._ModuleBase__ModuleBaseMeta, cls).\
                __init__(name, bases, dict)

            # Bind to the module context.
            cls.__BindModule(name, dict)
            # Aggregate dependencies from subclasses.
            cls.__AggregateDependencies(bases, dict.get('Dependencies'))
            # Implement ArgInfo support: if ArgInfo specified, use it to
            # automatically annotate the __init__ method.
            if 'ArgInfo' in dict:
                cls.__init__ = annotate_args(cls.ArgInfo)(cls.__init__)
            # Finally mark this instance as not yet instantiated.
            cls._Instantiated = False
            

        def __BindModule(cls, name, dict):
            if dict.get('BaseClass'):
                # This is a base class, not designed for export from a
                # module.  We suppress the ModuleName attribute.
                assert not hasattr(cls, 'ModuleName'), \
                    'Base classes cannot be tied to modules'
            else:
                cls.BaseClass = False
                # A normal implementation class.  This needs to be tied to a
                # particular module.
                if ModuleVersion._LoadingModule is None:
                    # Module is being defined as part of the build script, not
                    # in the module.  In this case if the class doesn't
                    # already have a module name specified we'll automatically
                    # name it after itself.
                    if not hasattr(cls, 'ModuleName'):
                        cls.ModuleName = name
                else:
                    # If we're called while loading a module then force the
                    # module name to agree with the loading module: in other
                    # words, an EPICS module isn't allowed to create classes
                    # which belong to other modules.
                    name = ModuleVersion._LoadingModule.Name()
                    if 'ModuleName' in dict:
                        assert cls.ModuleName == name, \
                            'ModuleName must be %s' % name
                        print 'Redundant ModuleName for', cls.__name__
                    cls.ModuleName = name
                cls.ModuleVersion = _ModuleVersionTable[cls.ModuleName]
                cls.ModuleVersion.ClassesList.append(cls)

        def __AggregateDependencies(cls, bases, Dependencies):
            if Dependencies:
                for base in bases:
                    dependency = base.__dict__.get('Dependencies')
                    if dependency:
                        # Note that it's important that the base class
                        # dependencies are instantiated first.
                        Dependencies = dependency + Dependencies
                cls.Dependencies = Dependencies

    __metaclass__ = __ModuleBaseMeta

    # The BaseClass attribute should be set to True in classes which are
    # intended to be base classes for other classes, and which are not
    # indended to be instantiated.
    BaseClass = True

    # Dependencies are used to trigger relationships between classes.
    # Dependencies are triggered when the class is first instantiated.
    Dependencies = ()
    # If this flag is set it allows this class to be automatically
    # instantiated if necessary.
    AutoInstantiate = False

    # Set of instantiated modules as ModuleVersion instances
    _ReferencedModules = set()

    @classmethod
    def _AutoInstantiate(cls):
        '''This can be called to ensure that an instance of the invoked class
        exists.'''
        # Note that, as the metaclass constructor ensures each class has its
        # own instance of this flag, we're always checking our own status,
        # not that of a base class!
        if not cls._Instantiated:
            assert cls.AutoInstantiate, \
                'Class %s cannot be automatically instantiated' % cls.__name__
            cls()

    @classmethod
    def UseModule(cls):
        '''This method is designed as a hook to be called exactly once before
        any instances of this class are created.  It will also walk the
        Dependencies list, ensuring that all the depencencies are also
        instantiated.'''
        for dependency in cls.Dependencies:
            dependency._AutoInstantiate()
        cls._ReferencedModules.add(cls.ModuleVersion)

    def __new__(cls, *args, **kargs):
        if not cls.__dict__['_Instantiated']:
            cls._Instantiated = True
            cls.UseModule()
        return cls.__super.__new__(cls, *args, **kargs)

        
    @classmethod
    def LibPath(cls, macro_name=False):
        '''Returns the path to the module.  If macro_name is set then a macro
        for the path is returned, otherwise the true path is returned.'''
        return cls.ModuleVersion.LibPath(macro_name = macro_name)

    @classmethod
    def ModuleFile(cls, filename):
        '''Returns an absolute path to a file within this module.'''
        return cls.ModuleVersion.ModuleFile(filename)

    @classmethod
    def ListModules(cls):
        '''Returns the set of all modules that have been instantiated.  The
        objects returned are ModuleVersion instances.'''
        return cls._ReferencedModules


def autodepends(*devices):
    '''This is a decorator helper function designed to be used with functions
    which require resources from one or more ModuleBase subclasses.  This is
    designed to be used as shown in the following exampe

        class resampleLib(Device):
            Dependencies = (genSub,)
            LibFileList = ['diagToolsResample']
            AutoInstantiate = True

        @autodepends(resampleLib)
        def ResampleWaveform(name, ...):
            return records.genSub(name,
                INAM = 'initResampleWaveform', ...)

    Here resampleLib wraps a library of calls designed to be used with genSub
    (hence the genSub dependency).  The autodepends(...) decoration ensures
    that records.genSub is available, as is the INAM argument.'''
    def device_wrapper(f):
        def wrapped_function(*args, **kargs):
            for device in devices:
                device._AutoInstantiate()
            return f(*args, **kargs)
        wrapped_function.__name__ = f.__name__
        wrapped_function.__doc__  = f.__doc__
        return wrapped_function
    return device_wrapper


def annotate_args(arg_info):
    '''This is a decorator helper function designed to add argument
    meta-information to a function.  The given arg_info is a list of arguments
    with associated name, type, description and optional default value, for
    example:

        @annotate_args((
            ('arg1', int, 'First argument'),
            ('arg2', bool, 'Last argument', False)))
        def function(arg1, arg2):
            print arg1, arg2
    '''
    def maybe_call(f, v):
        if f is None:
            return v
        else:
            return f(v)
    
    def annotater(f):
        def wrapped_function(*args, **kargs):
            call_args = {}
            # First the unnamed arguments, take them from the start of the
            # arg_info list.
            for arg, value in zip(arg_info, args):
                call_args[arg[0]] = maybe_call(arg[1], value)
            # Then the remaining arguments, defaulting any as appropriate.
            for arg in arg_info[len(call_args):]:
                try:
                    value = kargs.pop(arg[0])
                except KeyError:
                    if len(arg) > 3:
                        # If default available use the default, otherwise
                        # ignore this argument.
                        call_args[arg[0]] = maybe_call(arg[1], arg[3])
                else:
                    call_args[arg[0]] = maybe_call(arg[1], value)
            assert not kargs, 'Unexpected arguments: %s' % kargs.keys()

            return f(**call_args)
            
        wrapped_function.__name__ = f.__name__
        wrapped_function.__doc__  = f.__doc__
        wrapped_function.ArgInfo = arg_info
        return wrapped_function
    return annotater


# Dictionary of all modules with announced versions.  This will be
# interrogated when modules are initialised.
_ModuleVersionTable = {}

# We maintain all loaded modules in a synthetic module.
modules = CreateModule('iocbuilder.modules')
modules.LoadedModules = {}
