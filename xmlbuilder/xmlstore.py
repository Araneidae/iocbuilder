from PyQt4.QtGui import QUndoGroup
from PyQt4.QtCore import Qt, QString, SIGNAL
from xmltable import Table
import xml.dom.minidom, sys, os, traceback, time

class Store(object):
    def __init__(self, debug = False, DbOnly = False, doc = False,
            arch = 'vxWorks-ppc604_long'):
        # This is a default architecture
        self.architecture = arch
        self.simarch = False
        self.epics_base = None
        self.build_root = '.'
        self.iocname = 'example'
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
        # create our dict of classes
        classes = iocbuilder.includeXml.createClassLookup()
        # now we can make our tables
        for name, o in classes.items():
            # make a table object
            table = Table(o, self)
            # add it to our internal dict of tables
            self._tables[name] = table
            # add the undo stack
            self.stack.addStack(table.stack)
            # connect its modified signal to store a timestamp
            table.connect(table, SIGNAL(
                'dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.setLastModified)
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
        # proccess each component in turn
        problems = []
        warnings = []
        commentText = ""
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
                    # treat this as a comment on the next node
                    commentText = str(node.nodeValue)
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
                    pass
                elif self._tables.has_key(obname.replace("auto_", "")):
                    node.nodeName = obname.replace("auto_", "")
                    obname = str(node.nodeName)
                else:
                    problems.append(obname)
                    continue
                table = self.getTable(obname)
                if obname not in self._tableNames:
                    self._tableNames.append(obname)
                # make a new row
                warnings += table.addNode(node, commented, commentText)
                commentText = ""
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
