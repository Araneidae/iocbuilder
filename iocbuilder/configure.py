'''IOC builder configuration and initialisation.'''

import os

from support import Singleton
import recordnames


__all__ = [
    'Configure', 'LoadVersionFile', 'ConfigureIOC', 'ConfigureTemplate',
    'Architecture', 'TargetOS', 'Call_TargetOS',
    'ParseEtcArgs', 'ParseRelease']


def Architecture():
    return Configure.architecture

    
# Returns the target OS for the configured architecture, currently either
# linux or vxWorks.
def TargetOS():
    return Architecture().split('-', 1)[0]

def Get_TargetOS(self, name, *default):
    return getattr(self, '%s_%s' % (name, TargetOS()), *default)
    
    
# Helper function for calling a target OS specific function.  Looks up
#     self.<name>_<TargetOS()>
# and calls it with the given arguments if found, otherwise returns None.
def Call_TargetOS(self, name, *args, **kargs):
    try:
        method = Get_TargetOS(self, name)
    except AttributeError:
        return None
    else:
        return method(*args, **kargs)


## Central IOC builder configuration settings.
class Configure(Singleton):
    # Ensure we don't have to cope with multiple reconfigurations.
    __called = False

    
    ## This is the lowest level IOC builder initialisation function.
    #
    # Typically this function should not be called directly, instead one of
    # its proxies, \ref ConfigureIOC(), \ref ConfigureTemplate() or \ref
    # ParseEtcArgs(), must be called before any other builder functions are
    # called.  This function completes the configuration of the IOC builder
    # and initialisation of the builder's name space.
    #
    # \param module_path
    #   This configures where ModuleVersion() will look for modules.  By
    #   default the setting configured in \ref paths is used.
    # \param record_names
    #   This configures the record naming convention.  For examples see \ref
    #   recordnames.BasicRecordNames "BasicRecordNames", the simplest
    #   format, \ref recordnames.TemplateRecordNames "TemplateRecordNames"
    #   for naming templates, and \ref recordnames.DiamondRecordNames
    #   "DiamondRecordNames" for normal IOC generation.
    # \param ioc_writer
    #   This configures how IOCs are written.  Possible options are \ref
    #   iocwriter.SimpleIocWriter "SimpleIocWriter" for writing standalone
    #   databases or \ref iocwriter.DiamondIocWriter "DiamondIocWriter" for
    #   standard DLS IOCs.
    # \param dynamic_load
    #   This flag configures whether support modules are linked in or loaded
    #   at run-time.  Probably now obsolete, as static linking is now the
    #   rule.
    # \param architecture
    #   Configures the target architecture.  Must be set if an IOC is to be
    #   generated, not required for template only generation.
    # \param register_dbd
    #   Whether to call the register database function in the startup script.
    #   Like \c dynamic_load, probably obsolete.
    # \param simulation
    #   Controls whether simulation module definitions are to be selected.
    # \param epics_base
    #   Can be used to override the default selection of \c EPICS_BASE taken
    #   from the environment.
    def __call__(self,
            module_path  = None,    # Configures where ModuleVersion looks
            record_names = None,    # Configure how records are named
            ioc_writer   = None,    # Configure how IOCs are written
            dynamic_load = False,   # Configure how IOCs are built
            architecture = 'none',  # Configure target architecture
            register_dbd = False,   # Call register function in st.cmd?
            simulation = False,     # Enable simulation mode
            epics_base = None,      # Path to EPICS base, overrides env
        ):

        assert not self.__called, 'Cannot call Configure more than once!'
        self.__called = True

        import paths
        import libversion
        import iocinit
        import recordnames
        import iocwriter

        self.architecture = architecture
        libversion.simulation_mode = simulation

        if epics_base:
            # If epics_base is explicitly specified, override it now
            paths.SetEpicsBase(epics_base)
        assert hasattr(paths, 'EPICS_BASE'), \
            'Must specify EPICS_BASE in environment or in Configure call'

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


## Loads a list of module version declarations.
#
# This function is used to load a set of \ref libversion.ModuleVersion
# "ModuleVersion()" definitions.  The given file is executed with only
# ModuleVersion() in scope; no other calls or definitions should occur in the
# file.
#
# \param filename
#   This is the name of the file to be loaded.
# \param **context
#   Further symbols can be passed through to the loaded file, however this is
#   not recommended for normal use.
def LoadVersionFile(filename, **context):
    from libversion import ModuleVersion
    execfile(filename, dict(context,
        ModuleVersion = ModuleVersion,
        __file__ = filename))


# Some sensible default configurations.


## Normal IOC builder initialisation function.
#
# This function should normally be called before any other builder calls to
# complete configuration of the IOC builder.  By default the \c vxWorks
# architecture is selected and the DLS record naming convention is used for
# record names; these can both be overridden.
#
# \param architecture
#   Architecture of target system, defaults to \c 'vxWorks-ppc604_long'
# \param record_names
#   Class used to define record naming convention, defaults to standard
#   Diamond naming convention 
# \param **kargs
#   See \ref Configure.__call__() "Configure()" for other arguments that can
#   be passed.
def ConfigureIOC(
        architecture = 'vxWorks-ppc604_long',
        record_names = recordnames.DiamondRecordNames,
        **kargs):
    import iocwriter
    Configure(
        record_names = record_names(),
        ioc_writer   = iocwriter.DiamondIocWriter,
        architecture = architecture,
        register_dbd = True,
        **kargs)


## Function for configuring builder for template generation.
#
# This function can be used to configure the IOC builder for template
# generation.  By default record names are of the form
# <tt>\$(DEVICE):\<name></tt> using the \ref recordnames.TemplateRecordNames
# "TemplateRecordNames()" naming convention.
#
# If this call is used to initialise the builder only database files can be
# written using the builder using \ref
# iocwriter.SimpleIocWriter.WriteRecords() "WriteRecords()".
#
# \param record_names
#   An alternative naming convention can be specified, the default is
#   \ref recordnames.TemplateRecordNames "TemplateRecordNames()".
def ConfigureTemplate(record_names = None):
    import recordnames
    if record_names is None:
        record_names = recordnames.TemplateRecordNames()
    Configure(record_names = record_names)
    

def ParseRelease(dependency_tree, release, sup_release=None, debug=False):
    '''Read release, and create a dependency tree from it. If sup_release is a
    valid release file, then add it as a new dependency to the tree. Flatten
    the tree, and do the corresponding ModuleVersion call for each leaf in it. 
    Return a list of ModuleVersion objects. If debug then print the 
    ModuleVersion call made'''
    ## The list of ModuleVersions to return
    vs = []
    # If we have a release file, then parse it
    if os.path.isfile(release):
        tree = dependency_tree(None, release, includes=False, warnings=False)
    else:
        tree = dependency_tree(None, warnings=False)
    # if we have a sup_release then add it to the tree
    if os.path.isfile(sup_release):
        leaf = dependency_tree(tree, sup_release, includes=False, 
            warnings=False)
        tree.leaves.append(leaf)
    # print the tree if requested
    if debug:
        print '# Generated RELEASE tree'
        tree.print_tree()       
    # now flatten the leaves of the tree, and remove duplicates
    leaves = []
    for leaf in tree.flatten(include_self=False):
        duplicates = [ l for l in leaves if l.name == leaf.name ]
        if duplicates:
            print '***Warning: Module "%s" defined with' % leaf.name, \
                'multiple versions, using "%s"' % duplicates[0].version
        else:
            leaves.append(leaf)
    # now do our ModuleVersion calls       
    from libversion import ModuleVersion    
    for name, version, path in [(l.name, l.version, l.path) for l in leaves]:
        # for work and local modules, just tell iocbuilder the path
        if version in ['work', 'local']:
            home = os.path.abspath(path)
            use_name = False
            version = None
        # invalid modules don't have a configure/RELEASE, so won't have a 
        # builder object
        elif version == 'invalid':
            continue
        # prod modules need more hacking of the path to look right
        else:
            home = os.path.abspath(os.path.join(path, '..', '..'))
            use_name = True
        # iocs need to be treated more like support modules
        if '/' in name:
            name = name.split('/')[-1]
        # print out the ModuleVersion call if asked
        if debug:
            print 'ModuleVersion(%s, %s, use_name=%s, home=%s)' % (
                repr(name), repr(version), repr(use_name),
                repr(home))    
        # add the ModuleVersion object to the list    
        vs.append(ModuleVersion(name, version, use_name=use_name, 
                home=home))
    return vs                        



## An options parser for the standard gui options.
def ParseEtcArgs(dependency_tree=None, architecture = 'vxWorks-ppc604_long'):
    '''Does the following:
    * Parse sys.argv using the options parser
    * Run Configure with the supplied information
    * Parse <iocname>_RELEASE if it exists and do ModuleVersion calls from it
    * Return the options object
    The options object has the following attributes:
    * iocname: the name of the ioc that is to be built
    * iocpath: the path to the ioc directory
    * debug: if True, then debugging should happen
    * simarch: the architecture'''
    # first parse the normal options
    from optparse import OptionParser
    parser = OptionParser('''usage: %prog [options] <ioc_name>
    
This program will configure iocbuilder to write an ioc structure. It should
be run from the etc/makeIocs directory, and will create iocs/<ioc_name>''')
    parser.add_option('-d', action='store_true', dest='debug', 
        help='Print lots of debug information')
    parser.add_option('--sim', dest='simarch', 
        help='Create an ioc with arch=SIMARCH in simulation mode')
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error(
            '*** Error: Incorrect number of arguments ' 
            '- you must the IOC name as input')
    # store the ioc name and path            
    options.iocname = args[0]    
    options.iocpath = os.path.abspath(
        os.path.join('..', '..', 'iocs', options.iocname))                
    if options.simarch:          
        options.iocpath += '_sim'    
        architecture = options.simarch   
    # do the relevant configure call
    import iocwriter        
    Configure(
        record_names = recordnames.BasicRecordNames(),
        ioc_writer   = iocwriter.DiamondIocWriter, 
        dynamic_load = False, 
        architecture = architecture, 
        register_dbd = True, 
        simulation   = options.simarch)
    
    # Parse a RELEASE file to do the ModuleVersion calls
    if dependency_tree is not None:
        ParseRelease(dependency_tree,
            options.iocname + '_RELEASE', '../../configure/RELEASE',
            options.debug)    
    return options
