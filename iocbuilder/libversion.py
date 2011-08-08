'''Core definitions for modules.  Defines ModuleVersion version management
and ModuleBase base class.'''

import os
import sys
import string
import re
import types

import support
import hardware
import paths


__all__ = [
    'ModuleVersion', 'ModuleBase', 'modules', 'autodepends',
    'SetSimulation', 'DummySimulation']



# Checks for a Python module or package at path/module, returns the path to
# the python path to execute and a flag indicating whether the file is a
# package.
def _CheckPythonModule(path, module):
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

# Converts an arbitrary string into a valid Python identifier.
def PythonIdentifier(name):
    name = _ValidNameChars.sub('_', name)
    if len(name) == 0 or name[0] in set(string.digits):
        name = '_' + name
    return name


# Enable debugging
Debug = False



## Specifies module version and imports definitions.
#
# Declares the version of an EPICS support module and loads its definitions
# from the appropriate \c builder.py file into the \c iocbuilder namespace.
#
# The arguments are:
#
# \param libname
#     Name of the support module.  This will be upper-cased to form the
#     \c configure/RELEASE macro name.
# \param version
#     Version of support module to be loaded, if specified: names a
#     subdirectory of the support module directory.
# \param home
#     Directory where the support module is located.  If not specified
#     then \c EPICS_BASE
# \param use_name
#     If set (by default) the support module is located as a
#     subdirectory of home; if false, home (possibly plus version) is
#     the path to the support module.
# \param suppress_import
#     If set no builder definitions are loaded for this module.  Not
#     normally very useful!
# \param load_path
#     Can be used to specify the path to the builder definitions for this
#     module.  Otherwise the builder definitions are searched for in the
#     following locations:
# \code
#         <module>/etc/builder
#         <module>/builder
#         <iocbuilder>/defaults/<module>
# \endcode
# \param override
#     Can be set to allow definitions for a particular module to be
#     loaded more than once.  May not always work as expected, in
#     particular the old module definitions are not deleted first!
# \param auto_instantiate
#     If set then all ModuleBase subclasses marked as AutoInstantiate
#     will be instantiated as soon as this module's definitions have
#     been loaded.
class ModuleVersion:
    # Set of module macro names already allocated, used to ensure no clashes.
    __MacroNames = set()

    # This is set while the module is being loaded so that we can detect
    # nested loads (really bad idea) and can treat the module name specially
    # in ModuleBase.
    _LoadingModule = None
    # This is set to the list of auto-instantiating ModuleBase subclasses
    # that have been loaded so that we can auto instantiate them if
    # requested.
    _AutoInstances = []

    def __init__(self, libname,
            version=None, home=None, use_name=True,
            suppress_import=False, load_path=None, override=False,
            auto_instantiate=False):
        if Debug:
            print 'ModuleVersion(%s, version=%s, home=%s, ...) =>' % \
                tuple(map(repr, [libname, version, home])),

        if home is None:
            # By default pick up each module from the prod support directory.
            # It might be quite nice to extend this with a path search.
            home = paths.module_path
        else:
            # Normalise the path for safety.
            home = os.path.realpath(home)
        assert home and os.path.isdir(home), \
            'Invalid module home directory %s' % home

        self.__name = libname
        self.__module_name = PythonIdentifier(libname)
        self.version = version
        self.home = home
        self.use_name = use_name

        if Debug:
            print repr(self.LibPath())

        self.__macroname = PythonIdentifier(libname.upper())
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
            print >>sys.stderr, 'Import of %s skipped' % self.__name
        else:
            ModuleVersion._AutoInstances = []
            self.__LoadModuleDefinitions(load_path)
            if auto_instantiate:
                for subclass in ModuleVersion._AutoInstances:
                    subclass._AutoInstantiate()


    ## Returns the path to the module directory defined by this entry.
    #
    # \param macro_name
    #   If set to True then the module path is returned as a macro
    #   expression.  By default a true absolute filename to the module
    #   location is returned.
    def LibPath(self, macro_name=False):
        if macro_name:
            return '$(%s)' % self.__macroname

        path = self.home
        if self.use_name:
            path = os.path.join(path, self.__name)
        if self.version:
            path = os.path.join(path, self.version)
        return path

    ## Returns an absolute path to a file within this module.
    #
    # \param filename
    #   Name of file to be returned.  This call will fail of \c filename
    #   cannot be found in the module.
    def ModuleFile(self, filename):
        filename = os.path.join(self.LibPath(), filename)
        assert os.access(filename, os.R_OK), 'File "%s" not found' % filename
        return filename

    ## Returns the EPICS name of this module.
    def Name(self):
        return self.__name

    ## Returns the EPICS macro name used to identify this module.
    def MacroName(self):
        return self.__macroname

    ## Returns the Python identifier naming this module.  This is the EPICS
    # module name converted to a valid Python identifier.
    def ModuleName(self):
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
        self.module = support.CreateModule(ModuleName)
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
                # First look for a builder package in etc dir
                (os.path.join(self.LibPath(), 'etc'), 'builder'),
                # Then in the module root
                (self.LibPath(), 'builder'),
                # Failing that, try for a defaults entry.
                (support.SameDirFile(__file__, 'defaults'), self.__name)]
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
        elif Debug:
            print 'Module definitions for', self.__name, 'not found'



## All entities which need to depend on module versions should subclass
# this class to obtain access to their configuration information.
#
# By default the name of the class will be used both as an index into the
# ModuleVersion entry and as the subdirectory name in the support directory.
# When the external name of the module doesn't match the class name then
# the symbol \c ModuleName should be set equal to the external module name
# thus:
# \code
#     ModuleName = 'true-module-name'
# \endcode
#
# This class will always define a \c ModuleName symbol.  If the same module
# is to be used by all subclasses then this can be enabled by defining the
# symbol
# \code
#     InheritModuleName = True
# \endcode
#
# Note that this class is not normally subclassed outside of the IOC builder.
class ModuleBase(support.autosuper):

    # Class initialisation.

    def __init_meta__(cls, subclass):
        dict = cls.__dict__

        # Bind to the module context.
        cls.__BindModule(cls.__name__, dict)
        # Aggregate dependencies from subclasses.
        cls.__AggregateDependencies(cls.__bases__, dict.get('Dependencies'))
        # Remember this new class
        cls.ModuleBaseClasses.append(cls)
        # Finally mark this instance as not yet instantiated.
        cls._Instantiated = False

        if Debug:
            print 'ModuleBase subclass %s.%s' % (
                getattr(cls, 'ModuleName', 'iocbuilder'), cls.__name__)

    @classmethod
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
                # Module is being defined as part of the build script, not in
                # the module.  In this case if the class doesn't already have
                # a module name specified we'll automatically name it after
                # itself.
                if not hasattr(cls, 'ModuleName'):
                    cls.ModuleName = name
            else:
                # If we're called while loading a module then force the module
                # name to agree with the loading module: in other words, an
                # EPICS module isn't allowed to create classes which belong to
                # other modules.
                name = ModuleVersion._LoadingModule.Name()
                if 'ModuleName' in dict:
                    assert cls.ModuleName == name, \
                        'ModuleName must be %s' % name
                    print 'Redundant ModuleName for', cls.__name__
                    assert False
                cls.ModuleName = name
                # During module loading, also add class to list of classes to
                # auto instantiate.
                if cls.AutoInstantiate:
                    ModuleVersion._AutoInstances.append(cls)
            cls.ModuleVersion = _ModuleVersionTable[cls.ModuleName]
            cls.ModuleVersion.ClassesList.append(cls)

    @classmethod
    def __AggregateDependencies(cls, bases, Dependencies):
        if Dependencies:
            for base in bases:
                dependency = base.__dict__.get('Dependencies')
                if dependency:
                    # Note that it's important that the base class
                    # dependencies are instantiated first.
                    Dependencies = dependency + Dependencies
            cls.Dependencies = Dependencies


    ## The BaseClass attribute should be set to True in classes which are
    # intended to be base classes for other classes, and which are not
    # indended to be instantiated.
    BaseClass = True

    ## Dependencies are used to trigger relationships between classes.
    # Dependencies are triggered when the class is first instantiated.
    Dependencies = ()
    ## If this flag is set it allows this class to be automatically
    # instantiated if necessary.  Of course, the \c __init__ method must be
    # callable with no parameters if this flag is set.
    AutoInstantiate = False

    ## Set of instantiated modules as ModuleVersion instances
    _ReferencedModules = set()
    ## List of subclasses (direct or indirect)
    ModuleBaseClasses = []
    ## List of instantiated classes
    _ReferencedClasses = []
    ## List of all instances
    _ModuleBaseInstances = []

    # This can be called to ensure that an instance of the invoked class
    # exists.
    @classmethod
    def _AutoInstantiate(cls):
        # Note that, as the class initialisation ensures each class has its
        # own instance of this flag, we're always checking our own status,
        # not that of a base class!
        if not cls._Instantiated:
            assert cls.AutoInstantiate, \
                'Class %s cannot be automatically instantiated' % cls.__name__
            cls()

    ## This method is designed as a hook to be called exactly once before
    # any instances of this class are created.  It will also walk the
    # Dependencies list, ensuring that all the depencencies are also
    # instantiated.
    @classmethod
    def UseModule(cls):
        for dependency in cls.Dependencies:
            dependency._AutoInstantiate()
        cls._ReferencedClasses.append(cls)
        cls._ReferencedModules.add(cls.ModuleVersion)


    # This method is used to mark this class and all of its base classes as
    # instantiated: this is required to ensure that we don't accidentially
    # auto-instantiate base classes when we don't want to.  Note that
    # UseModule() is not invoked for the base classes.
    @classmethod
    def __mark_instantiated(cls):
        if cls.__dict__['_Instantiated']:
            return False
        else:
            cls._Instantiated = True
            for base in cls.__bases__:
                if '_Instantiated' in base.__dict__:
                    base.__mark_instantiated()
            return True

    def __new__(cls, *args, **kargs):
        if Debug:
            print 'Instantiating %s.%s(%s)' % (
                cls.ModuleName, cls.__name__, ', '.join(
                    map(repr, args) +
                    ['%s=%s' % (k, repr(v)) for k, v in kargs.items()]))

        if cls.__mark_instantiated():
            cls.UseModule()
        self = super(ModuleBase, cls).__new__(cls, *args, **kargs)
        cls._ModuleBaseInstances.append(self)
        return self


    ## Returns the path to the module.  If macro_name is set then a macro
    # for the path is returned, otherwise the true path is returned.
    @classmethod
    def LibPath(cls, macro_name=False):
        return cls.ModuleVersion.LibPath(macro_name = macro_name)

    ## Returns an absolute path to a file within this module.
    @classmethod
    def ModuleFile(cls, filename):
        return cls.ModuleVersion.ModuleFile(filename)

    ## Returns the set of all modules that have been instantiated.  The
    # objects returned are ModuleVersion instances.
    @classmethod
    def ListModules(cls):
        return cls._ReferencedModules

    # For every ModuleBase instance (or every sub-class if class_method
    # is True) checks for a method with the given name, and if found, calls
    # it.  Useful for binding events to all ModuleBase instances.
    @classmethod
    def CallModuleMethod(cls, name, class_method=False, **args):
        if class_method:
            l = cls._ReferencedClasses
        else:
            l = cls._ModuleBaseInstances
        for x in l:
            f = getattr(x, name, None)
            if f is not None:
                f(**args)


## This is a decorator helper function designed to be used with functions
# which require resources from one or more ModuleBase subclasses.  This is
# designed to be used as shown in the following example
#
# \code
#     class resampleLib(Device):
#         Dependencies = (genSub,)
#         LibFileList = ['diagToolsResample']
#         AutoInstantiate = True
#
#     @autodepends(resampleLib)
#     def ResampleWaveform(name, ...):
#         return records.genSub(name,
#             INAM = 'initResampleWaveform', ...)
# \endcode
#
# Here \c resampleLib wraps a library of calls designed to be used with \c
# genSub (hence the \c genSub dependency).  The \c autodepends(...) decoration
# ensures that \c records.genSub is available, as is the \c INAM argument.
def autodepends(*devices):
    def device_wrapper(f):
        def wrapped_function(*args, **kargs):
            for device in devices:
                device._AutoInstantiate()
            return f(*args, **kargs)
        wrapped_function.__name__ = f.__name__
        wrapped_function.__doc__  = f.__doc__
        return wrapped_function
    return device_wrapper


# Dictionary of all modules with announced versions.  This will be
# interrogated when modules are initialised.
_ModuleVersionTable = {}

## The module iocbuilder.modules contains every EPICS module that has been
# loaded.
#
# Every EPICS support module is added to \c modules using the module name
# converted to a Python identifier (by converting invalid characters to
# underscores).
modules = support.CreateModule('iocbuilder.modules')
modules.LoadedModules = {}


# Used to create simulation objects with no behaviour.
class DummySimulation(object):
    def __init__(self, **kwargs):
        self.args = kwargs


simulation_mode = False
## If we are in simulation mode, then place \c sim instead of \c real in
# iocbuilder.modules and ModuleBase.ModuleBaseClasses.
#
# \param real
#   Class installed by default
# \param sim
#   Replacement simulation class.
def SetSimulation(real, sim):
    if simulation_mode:
        # If no simulation, make a dummy one
        if sim is None:
            class new_sim(DummySimulation):
                pass
        else:
            # Try to subclass the sim object
            try:
                class new_sim(sim):
                    pass
            # It is probably a function, so just call it
            except TypeError, e:
                def new_sim(*args, **kwargs):
                    return sim(*args, **kwargs)

        # first replace it in the list of subclasses
        index = ModuleBase.ModuleBaseClasses.index(real)
        ModuleBase.ModuleBaseClasses[index] = new_sim
        # now in iocbuilder.modules
        for attr in [
                '__name__', 'ModuleName', 'ArgInfo', 'Defaults', 'Arguments',
                'UniqueName']:
            if hasattr(real, attr):
                setattr(new_sim, attr, getattr(real, attr))
        modulename = real.ModuleVersion.ModuleName()
        setattr(getattr(modules, modulename), real.__name__, new_sim)
        return new_sim
    else:
        # Remove it from the list of subclasses
        if sim in ModuleBase.ModuleBaseClasses:
            ModuleBase.ModuleBaseClasses.remove(sim)
        return real
