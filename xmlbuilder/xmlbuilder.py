#!/bin/env dls-python
import sys, os, shutil, glob
import re
from subprocess import *
from optparse import OptionParser
import xml.dom.minidom
from xmlconfig import XmlConfig


# hacky hacky change linux-x86 to linux-x86_64 in RHEL6
def patch_arch(arch):
    lsb_release = Popen(["lsb_release", "-sr"], stdout=PIPE).communicate()[0][0]
    if lsb_release == "6" and arch == "linux-x86":
        arch = "linux-x86_64"
    return arch


def main():
    parser = OptionParser('usage: %prog [options] <xml-file>')
    parser.add_option(
        '-d', action='store_true', dest='debug',
        help='Print lots of debug information')
    parser.add_option(
        '-D', action='store_true', dest='DbOnly',
        help='Only output files destined for the Db dir')
    parser.add_option('-o', dest='out',
        default=os.path.join('..', '..', 'iocs'),
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
        '-c', action='store_true', dest='no_check_release',
        help='Set CHECK_RELEASE to FALSE')
    parser.add_option(
        '-b', action='store_true', dest='no_substitute_boot',
        help='Don\'t substitute .src file to make a .boot file, copy it and '\
        ' create an envPaths file to load')
    parser.add_option(
        '--build-debug', action='store_true', dest='build_debug',
        help='Enable debug build of IOC')

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

    # read the xml text for the architecture
    xml_file = args[0]
    if options.debug:
        print '--- Parsing %s ---' % xml_file
    xml_text = open(xml_file).read()
    xml_root = xml.dom.minidom.parseString(xml_text)
    components = [n
        for n in xml_root.childNodes if n.nodeType == n.ELEMENT_NODE][0]
    if options.simarch is not None:
        architecture = patch_arch(options.simarch)
        simarch = architecture
    else:
        architecture = patch_arch(str(components.attributes['arch'].value))
        simarch = None

    # setup the XmlIocBuilder
    xml_config = XmlConfig(debug=debug, DbOnly=DbOnly,
                           doc=options.doc, arch=architecture,
                           simarch=simarch, filename=xml_file)
    xml_config.iocbuilder.SetSource(os.path.realpath(xml_file))
    xml_config.iocbuilder.SetAdditionalHeaderText(get_git_status(xml_file))

    # create iocbuilder objects from the xml text
    xml_config.iocbuilder.includeXml.instantiateXml(xml_text)

    if options.doc:
        iocpath = options.doc
    elif DbOnly:
        iocpath = os.path.abspath(".")
        if options.simarch:
            xml_config.iocname += '_sim'
    else:
        # write the iocs
        root = os.path.abspath(options.out)
        iocpath = os.path.join(root, xml_config.iocname)
        if options.simarch:
            iocpath += '_sim'
#            store.iocbuilder.SetEpicsPort(6064)

    substitute_boot = not options.no_substitute_boot
    if xml_config.architecture == "win32-x86":
        substitute_boot = False
    if debug:
        print "Writing ioc to %s" % iocpath
    xml_config.iocbuilder.WriteNamedIoc(iocpath,
                                        xml_config.iocname,
                                        check_release=not options.no_check_release,
                                        substitute_boot=substitute_boot,
                                        edm_screen=options.edm_screen,
                                        build_debug=options.build_debug)
    if debug:
        print "Done"

    # Check for README in same directory as source XML
    check_for_readme(xml_file, iocpath, xml_config.iocname, debug)


def readme_exists(xml_file, iocname, debug):
    readme_pattern = xml_file.replace(".xml", "_README*")
    readme_paths = glob.glob(readme_pattern)
    if len(readme_paths) > 0:
        # Return only the first match
        if debug:
            print("Found README at {path}".format(path=readme_paths[0]))
        return readme_paths[0]
    else:
        if debug:
            print("No README found")
        return None


def get_source_readme_filename(source_readme_path):
    split_path = source_readme_path.split("/")
    return split_path[-1]


def get_destination_readme_filename(source_readme_path):
    readme_filename = get_source_readme_filename(source_readme_path)
    extension_pos = readme_filename.find(".")
    destination_filename = "README"
    if extension_pos != -1:
        destination_filename += readme_filename[extension_pos:]
    return destination_filename


def check_for_readme(xml_file, iocpath, iocname, debug):
    # Check for README
    source_readme_path = readme_exists(xml_file, iocname, debug)
    if source_readme_path is not None:
        readme_filename = get_destination_readme_filename(source_readme_path)
        destination_readme_path = "{iocpath}/{filename}".format(
            iocpath=iocpath,
            filename=readme_filename)
        if debug:
            print("Copying README to {0}".format(destination_readme_path))
        shutil.copyfile(source_readme_path, destination_readme_path)


def get_git_status(source):
    git_status = ["Git status:"]
    source_path = os.path.dirname(source)
    xml_file = os.path.basename(source)
    release = os.path.splitext(xml_file)[0] + "_RELEASE"
    git_status += get_latest_commit(source_path)
    git_status += get_file_git_status([xml_file, release], source_path)
    return '\n'.join(git_status)


def get_latest_commit(repo_path):
    commit_info = []
    git_describe = 'git describe --tags --long --always'.split()
    git_log = 'git log -n 1 --pretty=format:%s'.split()
    try:
        description = check_output(git_describe, cwd=repo_path).strip()
        message = check_output(git_log, cwd=repo_path)
        commit_info.append('{} "{}"'.format(description, message))
    except CalledProcessError:
        commit_info.append('No git info')
    return commit_info


def get_file_git_status(file_list, repo_path):
    file_status = []
    git_lstree = 'git ls-tree -r --name-only HEAD'.split()
    git_diff = 'git diff --name-only HEAD'.split()
    try:
        tracked = check_output(git_lstree, cwd=repo_path)
        uncommitted = check_output(git_diff, cwd=repo_path)
        for f in file_list:
            if f not in tracked or f in uncommitted:
                file_status.append('{} contained uncommitted changes'\
                                   ' at build time'.format(f))
    except CalledProcessError:
        pass
    return file_status


if __name__=='__main__':
    # Pick up containing IOC builder
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(root)
    from pkg_resources import require
    require('dls_environment')
    require('dls_dependency_tree')
    require('dls_edm')
    main()
