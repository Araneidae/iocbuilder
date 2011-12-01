#!/bin/env python2.6
from xmlstore import Store
import sys, os
from optparse import OptionParser
import xml.dom.minidom

def main():
    parser = OptionParser('usage: %prog [options] <xml-file>')
    parser.add_option(
        '-d', action='store_true', dest='debug',
        help='Print lots of debug information')
    parser.add_option(
        '-D', action='store_true', dest='DbOnly',
        help='Only output files destined for the Db dir')
    parser.add_option('-o', dest='out',
        default = os.path.join('..', '..', 'iocs'),
        help='Output directory for ioc')
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
    store = Store(debug = debug, DbOnly = DbOnly, doc = options.doc)
    if options.debug:
        print '--- Parsing %s ---' % xml_file
    store.iocname = os.path.basename(xml_file).replace('.xml','')
    store.build_root = os.path.dirname(os.path.abspath(xml_file))

    xml_text = open(xml_file).read()
    xml_root = xml.dom.minidom.parseString(xml_text)
    components = [n
        for n in xml_root.childNodes if n.nodeType == n.ELEMENT_NODE][0]
    if options.simarch is not None:
        store.architecture = options.simarch
        store.simarch = store.architecture
    else:
        store.architecture = str(components.attributes['arch'].value)
        store.simarch = None
    store.New()
    store.iocbuilder.SetSource(os.path.realpath(xml_file))

    # open the Xml file
    store.iocbuilder.includeXml.instantiateXml(xml_text)

    if options.doc:
        iocpath = options.doc
    elif DbOnly:
        iocpath = os.path.abspath(".")
        if options.simarch:
            iocname += '_sim'
    else:
        # write the iocs
        root = os.path.abspath(options.out)
        iocpath = os.path.join(root, iocname)
        if options.simarch:
            iocpath += '_sim'
#            store.iocbuilder.SetEpicsPort(6064)

    substitute_boot = not options.no_substitute_boot
    if store.architecture == "win32-x86":
        substitute_boot = False
    if debug:
        print "Writing ioc to %s" % iocpath
    store.iocbuilder.WriteNamedIoc(iocpath, iocname, check_release = True,
        substitute_boot = substitute_boot, edm_screen = options.edm_screen)
    if debug:
        print "Done"

if __name__=='__main__':
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    from pkg_resources import require
    sys.path.append("/dls_sw/work/common/python/dls_edm")
    require('dls_dependency_tree')
#    require('dls_edm')
    main()
