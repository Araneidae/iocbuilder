'''Xml for creating instances of templated xml files.'''

from libversion import ModuleBase
import libversion
from autosubst import populate_class
import support
import dbd
import arginfo
import os
import xml.dom.minidom

__all__ = ['Xml']

## Subclass of Substitution that scans its template file to find the macros it
# uses, and creates an ArgInfo object from them.
class Xml(ModuleBase):
    BaseClass = True

    WarnMacros = False
    ## This is set to True to disable scanning of the template file in
    # other subclasses of this
    Scanned = False
    TemplateFile = None
    # List of all template files
    TemplateFiles = []
    Arguments = None

    def __init_meta__(cls, first_call):
        if cls.TemplateFile is not None:
            # populate ArgInfo, etc.
            path = cls.ModuleFile(
                os.path.join('etc', 'makeIocs', cls.TemplateFile))
            populate_class(cls, path)
            cls.TemplateFiles.append(path)
            cls.Scanned = True

    @classmethod
    def fromModuleVersion(cls, moduleVersion):
        '''Make autosubstitution objects for all files in the makeIocs dir
        of moduleVersion object'''
        path = os.path.join(moduleVersion.LibPath(), 'etc', 'makeIocs')
        if os.path.isdir(path):
            # for each xml file
            for xml in os.listdir(path):
                # make sure it is an xml file
                if not xml.endswith('.xml'):
                    continue
                # make sure we haven't already made a custom builder object
                # for it
                if os.path.join(path, xml) in cls.TemplateFiles:
                    continue
                # make an Xml for it
                clsname = libversion.PythonIdentifier(
                    'auto_xml_' + xml.split('.')[0])
                class temp(Xml):
                    ModuleName = moduleVersion.Name()
                    TemplateFile = xml
                    TrueName = clsname
                setattr(moduleVersion.module, clsname, temp)

    ## Creates an Xml instance with the given arguments.  The
    # arguments need to match the arguments expected by the template to
    # be expanded.
    def __init__(self, **args):
        self.__super.__init__()

        # If we have Defaults, then update the argdict with them
        if hasattr(self, 'Defaults'):
            args = dict(self.Defaults, **args)

        # Check that all the required arguments have been given: we can't do
        # template expansion unless every argument is specified.
        assert self.TemplateFile, 'Must specify template file'
        assert self.Arguments is not None, 'Must specify some Arguments'
        assert set(args) == set(self.Arguments), \
            'Arguments %s missing or not recognised' % \
                list(set(args).symmetric_difference(set(self.Arguments)))

        # Store the args
        self.args = args

        # read in the xml file
        xml = self.ModuleFile(
            os.path.join('etc', 'makeIocs', self.TemplateFile))
        xml_text = open(xml).read()

        # substitute the args
        if args:
            xml_text = support.msi_replace_macros(args, xml_text)

        # make iocbuilder objects
        if libversion.Debug:
            print '< Loading objects from %s >' % self.TemplateFile
        self.objects = instantiateXml(xml_text)
        if libversion.Debug:
            print '</ Loading objects from %s >' % self.TemplateFile


def constructArgDict(el, objects, classes, ident_lookup=True):
    # dict of args to return
    d = {}
    # name of object represented by this element
    name = None
    # get the object class
    obname = str(el.nodeName)
    assert obname in classes, 'Can\'t find object "%s"'% obname
    ob = classes[obname]
    # find the column representing name
    nameKey = getattr(ob, 'UniqueName', 'name')
    # see if this nameKey also needs to be passed to the object constructor
    needsNameKey = nameKey in ob.ArgInfo.descriptions
    # build up the arg dict
    for attr, value in el.attributes.items():
        attr = str(attr)
        value = str(value)
        # check if this is the name key
        if attr == nameKey:
            name = value
            # if we don't need the name, then continue
            if not needsNameKey:
                continue
        # check the attribute is a valid argument
        assert attr in ob.ArgInfo.descriptions, \
            '%s is not a valid argument for %s' %(attr, ob)
        desc = ob.ArgInfo.descriptions[attr]
        # if it is an ident look it up
        if getattr(desc, 'ident', False):
            if ident_lookup:
                assert value in objects, 'Can\'t find object %s' % value
                value = objects[value]
        # otherwise make it the right type
        elif desc.typ == bool:
            if value and value.lower() != 'false':
                value = True
            else:
                value = False
        elif desc.typ == str:
            value = value.decode('string_escape')
        else:
            value = desc.typ(value)
        # add it to the dict
        d[attr] = value
    return name, ob, d

def createClassLookup():
    classes = {}
    # create some record classes
    records = []
    for recordtype in dbd.records.GetRecords():
        cls = getattr(dbd.records, recordtype)
        simple = arginfo.Simple
        # construct an ArgInfo object
        argInfo = arginfo.makeArgInfo(
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
        # add it to our list
        records.append(o)
    # create the class dict
    for o in ModuleBase.ModuleBaseClasses + records:
        # make sure we have an ArgInfo
        if not hasattr(o, 'ArgInfo') or o.__name__.startswith('_'):
            continue
        # add it to our class dict
        name = o.ModuleName + '.' + o.__name__
        classes[name] = o
    return classes

def instantiateXml(xml_text, objects=None):
    if objects is None:
        objects = {}

    xml_root = xml.dom.minidom.parseString(xml_text)
    # find the root node
    components = support.elements(xml_root)[0]
    # create class dict
    classes = createClassLookup()
    # find elements under it
    for node in support.elements(components):
        # lookup arguments
        name, ob, d = constructArgDict(node, objects, classes)
        # instantiate it
        inst = ob(**d)
        # store it if we are given a name
        if name is not None:
            objects[name] = inst
            if libversion.Debug:
                print 'Setting %s = %s' %(name, inst)
    return objects
