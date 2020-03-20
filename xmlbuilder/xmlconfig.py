import sys, os


class XmlConfig(object):
    def __init__(self, debug=False, DbOnly=False,
                 doc=False, arch='vxWorks-ppc604_long',
                 simarch=False, filename=""):
        self.architecture = arch
        self.simarch = simarch
        self.epics_base = None
        # store the debug state
        self.debug = debug
        self.DbOnly = DbOnly
        self.doc = doc
        self.iocname = os.path.basename(filename).replace('.xml', '')
        if filename:
            self.build_root = os.path.dirname(os.path.abspath(filename))
        else:
            self.build_root = os.getcwd()
        if self.debug:
            print "IOC name: %s" % self.iocname
            print "Build root: %s" % self.build_root
        self.configureIocbuilder()

    def configureIocbuilder(self):
        # Now make sure there is no iocbuilder hanging around
        for k in [k for k in sys.modules if k.startswith('iocbuilder')]:
            del sys.modules[k]
        if 'iocbuilder' in globals():
            del(iocbuilder)
        # now do the import and configure of iocbuilder
        import iocbuilder
        if self.debug:
            print '# Creating IOC with Architecture %s' % (self.architecture)
        self.iocbuilder = iocbuilder
        self.ioc_writer = None
        if self.DbOnly:
            self.ioc_writer = iocbuilder.iocwriter.DbOnlyWriter
        elif self.doc:
            self.ioc_writer = iocbuilder.iocwriter.DocumentationIocWriter
        # do the moduleversion calls
        from dls_dependency_tree import dependency_tree
        vs = self.iocbuilder.ParseAndConfigure(self, dependency_tree)
        # create AutoSubstitutions and moduleObjects
        for v in vs:
            if self.debug:
                print 'Making auto objects from %s' % v.LibPath()
            iocbuilder.AutoSubstitution.fromModuleVersion(v)
            iocbuilder.Xml.fromModuleVersion(v)
