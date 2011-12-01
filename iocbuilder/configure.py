'''IOC builder configuration and initialisation.'''

import os

from support import Singleton
import recordnames


__all__ = [
    'Configure', 'LoadVersionFile', 'ConfigureIOC', 'ConfigureTemplate',
    'Architecture', 'TargetOS', 'Call_TargetOS',
    'ParseEtcArgs', 'ParseAndConfigure']


def Architecture():
    return Configure.architecture


# Returns the target OS for the configured architecture, currently either
# WIN32, Linux or vxWorks.
_TargetOSlookup = {
    'linux': 'Linux',
    'win32': 'WIN32',
    'vxWorks': 'vxWorks'
}
def TargetOS():
    '''Returns the proper target OS as used in the makefiles'''
    return _TargetOSlookup[Architecture().split('-', 1)[0]]

def Get_TargetOS(self, name, *default):
    targetos = Architecture().split('-', 1)[0]
    return getattr(self, '%s_%s' % (name, targetos), *default)
def Get_TargetOS_dict(dict, name, *default):
    targetos = Architecture().split('-', 1)[0]
    key = '%s_%s' % (name, targetos)
    if default:
        return dict.get(key, *default)
    else:
        return dict[key]


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

        if module_path is not None:
            # Override computed paths.module_path if a value is configured.
            paths.module_path = module_path

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
def ConfigureTemplate(record_names = None, device = None):
    import recordnames
    assert device is None or record_names is None, \
        'Does not make sense to give device and record_names together'
    if record_names is None:
        record_names = recordnames.TemplateRecordNames(device = device)
    Configure(record_names = record_names)



## An options parser for the standard gui options.
#
# \param architecture
#   Used to set the target architecture.
# \param epics_base
#   Can be used to override EPICS_BASE settings.
#
# Does the following:
#
# - Parse \c sys.argv using the options parser
# - Return the \c options object, and \c args[1:]
#
# The options object has the following attributes:
#
# - \c iocname: the name of the ioc that is to be built
# - \c iocpath: the path to the ioc directory
# - \c debug: if \c True, then debugging should happen
# - \c architecture: The architecture (e.g. linux-x86)
# - \c simarch: Equal to \c architecture if making a simulation, otherwise
#   \c None
# - \c epics_base: Path to EPICS_BASE
def ParseEtcArgs(
        architecture = 'vxWorks-ppc604_long', epics_base = None):
    # first parse the normal options
    from optparse import OptionParser
    parser = OptionParser('''\
usage: %prog [options] <ioc_name>

This program will configure iocbuilder to write an ioc structure. It should
be run from the etc/makeIocs directory, and will create iocs/<ioc_name>''')
    parser.add_option('-d', action='store_true', dest='debug',
        help='Print lots of debug information')
    parser.add_option('--doc', dest='doc',
        help='Write out information in format for doxygen build instructions')
    parser.add_option('-o', dest='out',
        default = os.path.join('..', '..', 'iocs'),
        help='Output directory for ioc')
    parser.add_option('-D', action='store_true', dest='DbOnly',
        help='Only output files destined for the Db dir')
    parser.add_option('--sim', dest='simarch',
        help='Create an ioc with arch=SIMARCH in simulation mode')
    parser.add_option('--arch', dest='architecture', default = architecture,
        help='Specify target system architecture')
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error(
            '*** Error: Incorrect number of arguments '
            '- you must the IOC name as input')
    # store the ioc name and path
    options.iocname = args[0]
    options.iocpath = \
        os.path.abspath(os.path.join(options.out, options.iocname))
    if options.simarch:
        options.iocpath += '_sim'
        options.architecture = options.simarch
    if options.doc:
        options.iocpath = options.doc
        import iocwriter
        options.ioc_writer = iocwriter.DocumentationIocWriter
    elif options.DbOnly:
        options.iocpath = os.path.abspath('.')
        import iocwriter
        options.ioc_writer = iocwriter.DbOnlyWriter
    else:
        options.ioc_writer = None
    options.epics_base = epics_base
    options.build_root = '.'
    return options, args[1:]


## Parse RELEASE files and setup iocbuilder using the information in them
#
# \param options
#   The \c options object returned from ParseEtcArgs()
# \param dependency_tree
#   If present will be used to parse module dependencies from
#   \c configure/RELEASE and other files.
#
# Does the following:
#
# - If \c dependency_tree then:
#  - Parse <tt>../../configure/RELEASE</tt>
#  - Substitute macros in <tt>\<iocname>_RELEASE</tt> using
#    <tt>../../configure/RELEASE</tt>
#  - Set \c options.epics_base
# - Run \ref iocbuilder.configure.Configure "Configure(...)" with the supplied
#   information from \c options
# - If \c dependecy_tree then:
#  - Do a libversion::ModuleVersion call for each module listed in the tree
#    created from <tt>\<iocname>_RELEASE</tt> and
#    <tt>../../configure/RELEASE</tt>
def ParseAndConfigure(options, dependency_tree=None):
    # if we have a dependency_tree class, then parse RELEASE file
    if dependency_tree is not None:
        # If we have a release file, then parse it
        release = os.path.join(
            options.build_root, '..', '..', 'configure', 'RELEASE')
        if os.path.isfile(release):
            tree = dependency_tree(None, release, warnings=False)
        else:
            tree = dependency_tree(None, warnings=False)
        # add any leaves in
        extra_release = os.path.join(
            options.build_root, options.iocname + '_RELEASE')
        if os.path.isfile(extra_release):
            class hacked_tree(dependency_tree):
                def init_version(self):
                    self.modules.update(tree.modules)
            extra_tree = hacked_tree(None, extra_release, warnings=False)
            if options.debug:
                print '# Release tree'
                tree.print_tree()
            if options.debug:
                print '# Extra tree'
                extra_tree.print_tree()
            tree.leaves += extra_tree.leaves
        # print the tree if requested
        if options.debug:
            print '# Generated RELEASE tree'
            tree.print_tree()
        if 'EPICS_BASE' in tree.macros:
            options.epics_base = tree.macros['EPICS_BASE']

    # do the relevant configure call
    if options.ioc_writer is None:
        import iocwriter
        options.ioc_writer = iocwriter.DiamondIocWriter
    Configure(
        record_names = recordnames.BasicRecordNames(),
        ioc_writer   = options.ioc_writer,
        dynamic_load = False,
        architecture = options.architecture,
        register_dbd = True,
        simulation   = options.simarch,
        epics_base   = options.epics_base)

    # set debugging
    import libversion
    libversion.Debug = getattr(options, 'debug', True)

    # do the ModuleVersion calls on a dependency tree
    vs = []
    if dependency_tree is not None:
        # now flatten the leaves of the tree, and remove duplicates
        leaves = []
        for leaf in tree.flatten(include_self=True):
            duplicates = [l for l in leaves if l.name == leaf.name]
            # invalid modules don't have a configure/RELEASE, so won't have a
            # builder object
            if leaf.version == 'invalid':
                continue
            elif duplicates:
                print '***Warning: Module "%s" defined with' % leaf.name, \
                    'multiple versions, using "%s"' % duplicates[0].version
            else:
                leaves.append(leaf)
        from libversion import ModuleVersion
        for name, version, path in [
                (l.name, l.version, l.path) for l in leaves if l.path]:
            # for work and local modules, just tell iocbuilder the path
            if version in ['work', 'local']:
                home = os.path.abspath(path)
                use_name = False
                version = None
            # prod modules need more hacking of the path to look right
            else:
                home = os.path.abspath(os.path.join(path, '..', '..'))
                use_name = True
            # iocs need to be treated more like support modules
            if '/' in name:
                name = name.split('/')[-1]
            # add the ModuleVersion object to the list
            vs.append(ModuleVersion(name, version, use_name=use_name,
                    home=home))

    return vs
