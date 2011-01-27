#!/bin/env python2.6

from PyQt4.QtGui import QUndoGroup
from PyQt4.QtCore import Qt, QString, SIGNAL
from xmltable import Table
import xml.dom.minidom, os, sys, traceback, time
from optparse import OptionParser

class Store(object):
    def __init__(self, debug = False, DbOnly = False, doc = False,
            arch = 'vxWorks-ppc604_long', edm_screen = False,
            substitute_boot = True):
        # This is a default architecture
        self.architecture = arch
        self.simarch = False
        self.epics_base = None
        self.build_root = '.'
        self.iocname = 'example'
        self.edm_screen = edm_screen
        self.substitute_boot = substitute_boot
        # This the group of undo stacks for each table
        self.stack = QUndoGroup()
        # this is a dict of tables
        self._tables = {}
        self._tableNames = []
        # store the debug state
        self.debug = debug
        self.DbOnly = DbOnly
        self.doc = doc
        self.setLastModified()
        # this is the list of objects provided by this module, for documentation
        self.moduleObjects = []
        # store the arch and tableNames so we know we're clean
        self.setStored()

    def setStored(self):
        self._storedarchitecture = self.architecture
        self._stored_tableNames = self._tableNames[:]
        for table in self._tables.values():
            table.stack.setClean()

    def isClean(self):
        if self._storedarchitecture !=  self.architecture:
            return False
        if len(self._stored_tableNames) != len(self._tableNames):
            return False
        for x,y in zip(self._tableNames, self._stored_tableNames):
            if x != y:
                return False
        return True

    def _objectName(self, o):
        # get a suitable string identifier for a ModuleBase object
        return o.ModuleName + '.' + o.__name__

    def lastModified(self):
        return self._lastModified

    def setLastModified(self, index1=None, index2=None):
        self._lastModified = time.time()

    def New(self):
        '''Create a new table list by setting up ModuleVersion calls according
        to paths in release'''
        # First clear up the undo stack
        for stack in self.stack.stacks():
            self.stack.removeStack(stack)
        # then clear the table list
        self._tables.clear()
        # then clear the display list
        self._tableNames = []
        self._stored_tableNames = []
        # Now make sure there is no iocbuilder hanging around
        for k in [ k for k in sys.modules if k.startswith('iocbuilder') ]:
            del sys.modules[k]
        if 'iocbuilder' in globals():
            del(iocbuilder)
        # now do the import and configure of iocbuilder
        import iocbuilder
        if self.debug:
            print '# Creating IOC with Architcture %s' % (self.architecture)
            if self.simarch:
                print '# Simulation mode'
            print 'from iocbuilder import ModuleVersion, records'
        self.ioc_writer = None
        if self.DbOnly:
            self.ioc_writer = iocbuilder.iocwriter.DbOnlyWriter
        elif self.doc:
            self.ioc_writer = iocbuilder.iocwriter.DocumentationIocWriter
        self.iocbuilder = iocbuilder
        # do the moduleversion calls
        from dls_dependency_tree import dependency_tree
        vs = self.iocbuilder.ParseAndConfigure(self, dependency_tree)
        # create AutoSubstitutions and moduleObjects
        for v in vs:
            if self.debug:
                print 'Making auto objects from %s' % v.LibPath()
            iocbuilder.AutoSubstitution.fromModuleVersion(v)
        # now we can make our tables
        for i,o in enumerate(iocbuilder.ModuleBase.ModuleBaseClasses):
            # make sure we have an ArgInfo
            if not hasattr(o, 'ArgInfo') or o.__name__.startswith('_'):
                continue
            # make a table object
            table = Table(o, self)
            # add it to our internal dict of tables
            self._tables[self._objectName(o)] = table
            # add the undo stack
            self.stack.addStack(table.stack)
            # connect its modified signal to store a timestamp
            table.connect(table, SIGNAL(
                'dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.setLastModified)
        # now make the record types
        for recordtype in iocbuilder.records.GetRecords():
            cls = getattr(iocbuilder.records, recordtype)
            simple = iocbuilder.arginfo.Simple
            argInfo = iocbuilder.arginfo.makeArgInfo(
                ['record'], cls.FieldInfo().keys(),
                record = simple('Record name', str),
                **cls.FieldInfo())
            class o(object):
                r = cls
                def __init__(self, record, **args):
                    self.r(record, **args)
                ModuleName = 'records'
                ArgInfo = argInfo
            o.__name__ = recordtype
            # make a table object
            table = Table(o, self)
            # add it to our internal dict of tables
            self._tables[self._objectName(o)] = table
            # add the undo stack
            self.stack.addStack(table.stack)
        self.setStored()
        # failure if there were no callables
        self.setLastModified()


    def Open(self, filename, sim = None):
        if self.debug:
            print '--- Parsing %s ---'%filename
        self.iocname = os.path.basename(filename).replace('.xml','')
        self.build_root = os.path.dirname(os.path.abspath(filename))
        # read the tables
        xml_root = xml.dom.minidom.parse(filename)
        # find the root node
        components = self._elements(xml_root)[0]
        if sim is not None:
            self.architecture = sim
            self.simarch = self.architecture
        else:
            self.architecture = str(components.attributes['arch'].value)
            self.simarch = None
        self.New()
        self.iocbuilder.SetSource(os.path.realpath(filename))
        # proccess each component in turn
        problems = []
        warnings = []
        for node in components.childNodes:
            # try to find the class of each component
            if node.nodeType == node.COMMENT_NODE:
                # If it's a comment, then mark as a comment and try to process
                # its content
                commented = True
                text = '<junk>'+node.toxml()[4:-3]+'</junk>'
                root = self._elements(xml.dom.minidom.parseString(text))[0]
                nodes = self._elements(root)
                if len(nodes) == 0:
                    continue
            elif node.nodeType == node.ELEMENT_NODE:
                # If it's an element node, then just add this node
                commented = False
                nodes = [node]
            else:
                # Ignore whitespace
                continue
            for node in nodes:
                # find the correct table
                obname = str(node.nodeName)
                if self._tables.has_key(obname):
                    table = self.getTable(obname)
                    if obname not in self._tableNames:
                        self._tableNames.append(obname)
                else:
                    problems.append(obname)
                    continue
                # make a new row
                warnings += table.addNode(node, commented)
        self.setStored()
        self.setLastModified()
        return self._unique(problems, warnings)

    def _unique(self, *ls):
        # make each list in args unique, then return a tuple of them
        ret = []
        for l in ls:
            newl = []
            for x in l:
                if x not in newl:
                    newl.append(x)
            ret.append(newl)
        return tuple(ret)

    def _elements(self,xml):
        return [n for n in xml.childNodes if n.nodeType == n.ELEMENT_NODE]

    def Save(self, filename):
        # write the tables to disk
        impl = xml.dom.minidom.getDOMImplementation()
        doc = impl.createDocument(None, 'components', None)
        # look at each table that is displayed
        for name in self._tableNames:
            table = self._tables[name]
            # make the xml elements and add them to doc
            table.createElements(doc, name)
        doc.documentElement.setAttribute('arch',self.architecture)
        text = doc.toprettyxml()
        open(filename,'w').write(text)
        self.setStored()

    def CreateIoc(self, iocpath, iocname):
        obs = {}
        if self.debug:
            print 'from iocbuilder.modules import *'
        for name in self._tableNames:
            table = self._tables[name]
            # make builder objects
            table.createObjects(obs)
        substitute_boot = self.substitute_boot
        if self.architecture == "win32-x86":
            substitute_boot = False
        self.iocbuilder.WriteNamedIoc(iocpath, iocname, check_release = True,
            substitute_boot = substitute_boot, edm_screen = self.edm_screen)

    def getTable(self, name):
        # return the table
        table = self._tables[name]
        self.stack.setActiveStack(table.stack)
        return table

    def allTableNames(self):
        return sorted(self._tables.keys())

    def setTableNames(self, names):
        self._tableNames = names

    def getTableNames(self):
        return self._tableNames

    def getArch(self):
        return self.architecture

    def setArch(self, arch):
        self.architecture = arch


def main():
    parser = OptionParser('usage: %prog [options] <xml-file>')
    parser.add_option(
        '-d', action='store_true', dest='debug',
        help='Print lots of debug information')
    parser.add_option(
        '-D', action='store_true', dest='DbOnly',
        help='Only output files destined for the Db dir')
    parser.add_option(
        '--doc', dest='doc',
        help='Write out information in format for doxygen build instructions')
    parser.add_option(
        '--sim', dest='simarch',
        help='Create an ioc with arch=SIMARCH in simulation mode')
    parser.add_option(
        '-e', action='store_true', dest='edm_screen',
        help='Try to create a set of edm screens for this module')
    parser.add_option(
        '-b', action='store_true', dest='no_substitute_boot',
        help='Don\'t substitute .src file to make a .boot file, copy it and '\
        ' create an envPaths file to load')

    # parse arguments
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error(
            '*** Error: Incorrect number of arguments - '
            'you must supply one input file (.xml)')

    # define parameters
    if options.debug:
        debug = True
    else:
        debug = False
    if options.DbOnly:
        DbOnly = True
    else:
        DbOnly = False

    # setup the store
    xml_file = args[0]
    iocname = os.path.basename(xml_file).replace('.xml','')
    store = Store(debug = debug, DbOnly = DbOnly, doc = options.doc,
        edm_screen = options.edm_screen, substitute_boot = not options.no_substitute_boot)
    problems, warnings = store.Open(xml_file, sim = options.simarch)
    for prob in problems:
        print '***Error:', prob
    for warn in warnings:
        print '***Warning:', warn

    if options.doc:
        store.CreateIoc(options.doc, iocname)
    elif DbOnly:
        iocpath = os.path.abspath(".")
        if options.simarch:
            iocname += '_sim'
        store.CreateIoc(iocpath, iocname)
    else:
        # write the iocs
        root = os.path.abspath(
            os.path.dirname(os.path.abspath(xml_file))+'/../../iocs/')
        iocpath = os.path.join(root, iocname)
        if options.simarch:
            iocpath += '_sim'
#            store.iocbuilder.SetEpicsPort(6064)
        store.CreateIoc(iocpath, iocname)

if __name__=='__main__':
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    from pkg_resources import require
    sys.path.append("/dls_sw/work/common/python/dls_edm")
    require('dls_dependency_tree')
#    require('dls_edm')
    main()
