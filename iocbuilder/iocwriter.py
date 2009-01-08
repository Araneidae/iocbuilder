'''The IOC writers defined here are designed to be passed to the library
Configure call as an 'iocwriter' argument.
'''

import sys, time
import os, os.path
import shutil
import types
import fnmatch

import iocinit
import recordset
import configure
import libversion
import hardware

from liblist import Hardware
from paths import msiPath


__all__ = ['IocWriter', 'SimpleIocWriter', 'DiamondIocWriter']



        
def PrintDisclaimer():
    now = time.strftime('%a %d %b %Y %H:%M:%S %Z')
    source = os.path.realpath(sys.argv[0])
    print \
'''# This file was automatically generated on %(now)s from
# source: %(source)s
#
# *** Please do not edit this file: edit the source file instead. ***
#''' % locals()



class WriteFile:
    '''A support routine for writing files using the print mechanism.  This is
    simply a wrapper around sys.stdout redirection.  Use this thus:
        output = WriteFile(filename)
        ... write to stdout using print etcetera ...
        output.Close()
    By default the standard disclaimer header is printed at the start of the
    generated file.'''

    def __init__(self, filename, header=PrintDisclaimer, maxLineLength=0):
        '''Set header=None to suppress header output.'''
        self.__stdout = sys.stdout
        self.__output = open(filename, 'w')
        self.__line = ''

        self.__maxLineLength = maxLineLength
        if self.__maxLineLength:
            sys.stdout = self
        else:
            sys.stdout = self.__output
        
        if header:
            header()

    def write(self, string):
        # Check that no line exceeds the maximum line length
        lines = string.split('\n')
        for line in lines[:-1]:
            full_line = self.__line + line
            self.__line = ''
            assert len(full_line) <= self.__maxLineLength, \
                'Line %s too long' % repr(full_line)
        self.__line = self.__line + lines[-1]
        
        self.__output.write(string)

    def Close(self):
        '''Call this to close the file being written and to restore normal
        output to stdout.'''
        assert self.__output != None, 'Close called out of sequence.'
        assert len(self.__line) <= self.__maxLineLength, \
            'Unterminated line %s too long' % repr(self.__line)
        self.__output.close()
        self.__output = None
        sys.stdout = self.__stdout



class IocWriter:
    '''Base class for IOC writer.  A subclass of this class should be passed
    as an iocwriter option to the epics.Configure method.
        Methods are provided for access to all of the resources which define
    an IOC.
    '''

    def __init__(self, iocRoot=''):
        self.iocRoot = iocRoot
        
        # Set up the appropriate methods for the actions required during IOC
        # writing.

        # Printout of records, autosave files and subsititution files
        self.PrintRecords = recordset.RecordSet.Print
        self.PrintAutosaves = recordset.RecordSet.PrintAutosaves
        self.PrintSubstitutions = recordset.SubstitutionSet.Print
        self.SortedTemplateList = recordset.SubstitutionSet.SortedTemplateList
        # Alternative to mass expand substitution files at build time
        self.ExpandSubstitutions = \
            recordset.SubstitutionSet.ExpandSubstitutions

        self.CountRecords = recordset.RecordSet.CountRecords
        self.CountAutosaves = recordset.RecordSet.CountAutosaves
        self.CountSubstitutions = recordset.SubstitutionSet.CountSubstitutions

        # Print st.cmd for IOC
        self.PrintIoc = iocinit.iocInit.PrintIoc

        # Add filename to list of databases known to this IOC
        self.AddDatabase = iocinit.iocInit.AddDatabaseName
        
        # Copies all files bound to IOC into given location
        self.SetDataPath = iocinit.IocDataFile.SetDataPath
        self.CopyDataFiles = iocinit.IocDataFile.CopyDataFiles
        self.DataFileCount = iocinit.IocDataFile.DataFileCount


    def SetIocName(self, ioc_name):
        iocinit.iocInit.SetIocName(ioc_name)

        
    def WriteFile(self, filename, writer, *argv, **argk):
        if not isinstance(filename, types.StringTypes):
            filename = os.path.join(*filename)
        output = WriteFile(
            os.path.join(self.iocRoot, filename), **argk)
        if callable(writer):
            writer(*argv)
        else:
            print writer
        output.Close()
        

    def ResetRecords(self):
        '''This method resets only the record data but not the remaining IOC
        state.  This should only be used if incremental record creation
        without building a new IOC is required.

        It is harmless to call this method repeatedly.'''
        recordset.Reset()



class SimpleIocWriter(IocWriter):
    '''This is the simplest possible IOC writer.  Two methods are supported,
    WriteRecords and WriteHardware, which write out respectively the set of
    generated records and the IOC startup script.'''

    __all__ = ['WriteRecords', 'WriteHardware']

    def WriteRecords(self, filename):
        '''Writes all the currently generated records to the given file.
        The set of records will be reset after this has been done.  The
        filename can be specified in two parts: the filename proper is
        written to the st.cmd file, while the file is written to
        path/filename if path is given.'''
        
        # Let the IOC know about this database.
        self.AddDatabase(filename)
        # Write out the database: record set and template expansions.  In
        # this version we fully expand template instances.
        self.WriteFile(filename, self.PrintAndExpandRecords)
        # Finally reset the two resources we've just consumed.
        self.ResetRecords()

    def PrintAndExpandRecords(self):
        self.PrintRecords()
        self.ExpandSubstitutions(msiPath)

    def WriteHardware(self, filename):
        '''Writes out the IOC startup command file.  The entire internal
        state (apart from configuration) is reset: this allows a new IOC
        application to be generated from scratch if required.'''

        self.WriteFile(filename, self.PrintIoc, maxLineLength=126)



class DiamondIocWriter(IocWriter):
    '''This IOC writer generates a complete IOC application tree in the
    Diamond 3.13 style.  This should be used in the following way:

        iocWriter = OpenIocWriter(<path-to-iocs>, <domain>, <technical-area>)
        for each ioc number:
            configure ioc settings
            generate ioc definitions
            iocWriter.WriteIoc(id)
        iocWriter.Close()

    '''

    __all__ = ['WriteIoc']
    

    IOC_configure_Skeleton = {
        'CONFIG':
'''include $(TOP)/configure/CONFIG_APP

BUILD_ARCHS = vxWorks-ppc604_long
''',

    'CONFIG_APP':
'''include $(TOP)/configure/RELEASE
-include $(TOP)/configure/RELEASE.$(EPICS_HOST_ARCH)
-include $(TOP)/configure/RELEASE.Common.$(T_A)
-include $(TOP)/configure/RELEASE.$(EPICS_HOST_ARCH).$(T_A)

CONFIG=$(EPICS_BASE)/configure
include $(CONFIG)/CONFIG
-include $(CONFIG)/CONFIG.Dls

INSTALL_LOCATION = $(TOP)
ifdef INSTALL_LOCATION_APP
INSTALL_LOCATION = $(INSTALL_LOCATION_APP)
endif

ifdef T_A
-include $(TOP)/configure/O.$(T_A)/CONFIG_APP_INCLUDE
endif

# dbst based database optimization (default: NO)
DB_OPT = NO
''',

        'Makefile':
'''TOP=..

include $(TOP)/configure/CONFIG

# Set the following to NO to disable consistency checking of
# the support applications defined in $(TOP)/configure/RELEASE
CHECK_RELEASE = YES

TARGETS = $(CONFIG_TARGETS)
CONFIGS += $(subst ../,,$(wildcard $(CONFIG_INSTALLS)))

include $(TOP)/configure/RULES
''',

        'RULES':
'''#CONFIG
-include $(CONFIG)/RULES.Dls
include  $(CONFIG)/RULES

# Library should be rebuilt because LIBOBJS may have changed.
$(LIBNAME): ../Makefile
''',

        'RULES_DIRS':
'''include $(EPICS_BASE)/configure/RULES_DIRS
''',

        'RULES.ioc':
'''include $(EPICS_BASE)/configure/RULES.ioc
''',

        'RULES_TOP':
'''include $(EPICS_BASE)/configure/RULES_TOP
''',
    }

    IOC_MAKEFILE_TEMPLATE = \
'''TOP=../..
include $(TOP)/configure/CONFIG
SCRIPTS += st%(ioc)s.boot
include $(TOP)/configure/RULES
%%.boot: ../%%.cmd
	cp $< $@
'''    

    @classmethod
    def WriteIoc(cls, *argv, **argk):
        cls(*argv, **argk)

    def MakeDirectory(self, *dir_names):
        os.makedirs(os.path.join(self.iocRoot, *dir_names))

        
    def __DeleteIocDirectory(self, domain, techArea):
        # Checks that the newly computed iocBoot directory is a plausible IOC
        # directory.  This prevents any unfortunate accidents caused by
        # accidentially pointing at some other directory by mistake...
        #    The only files we can absolutely expect to be present are the
        # configure and iocBoot directories (as these are created by
        # __init__), and we allow for all the built directories and our App
        # directories.  Anything else is suspicious!
        dirlist = os.listdir(self.iocRoot)
        require_list = ['configure', 'iocBoot']
        ignore_list = ['bin', 'db', 'dbd', 'Makefile', 'data'] + \
            fnmatch.filter(dirlist, '%s-%s-IOC-??App' % (domain, techArea))
        assert set(dirlist) - set(ignore_list) == set(require_list), \
            'Directory %s doesn\'t appear to be an IOC directory' % \
                self.iocRoot
        shutil.rmtree(self.iocRoot)
        

        
    def __init__(self, path, domain, techArea, id,
            make_boot = True, long_name = False):
        '''The Diamond style of IOC as supported by this writer is of the
        following form, where <ioc>=<domain>-<techArea>-IOC-<id> and <iocDir>
        is either <techArea> or <ioc> depending on whether long_name is set.
        
         <path>/<domain>/<iocDir>
           Makefile         Top level makefile to call <ioc>App Makefiles
           iocBoot/
             ioc<ioc>/      Directory for st.cmd and other ioc resources
               st<ioc>.cmd  IOC startup script
               <ioc files>  Other ioc specific files may be placed here
           <ioc>App/
             Makefile       Makefile to build IOC db directory and file
             Db/            Directory containing substitutions and other files
               <ioc>.db     Generated database file
               <ioc>.substitutions   Substitutions file

        The Makefile will create a db/ directory, copy the <ioc>.db file into
        it, and create an expanded <ioc>.expanded.db file.'''
        
        if long_name:
            iocDir = '%s-%s-IOC-%02d' % (domain, techArea, id)
        else:
            iocDir = techArea
        IocWriter.__init__(self, os.path.join(path, domain, iocDir))

        self.domain = domain
        self.techArea = techArea
        self.make_boot = make_boot
        self.id = id
        
        self.iocBoot = os.path.join(self.iocRoot, 'iocBoot')
        if os.access(self.iocRoot, os.F_OK):
            self.__DeleteIocDirectory(domain, techArea)
        self.MakeDirectory('')
        self.MakeDirectory('iocBoot')
        self.MakeDirectory('configure')

        # Create the data directory
#         self.MakeDirectory('data')
        self.SetDataPath('data')
        
        # Write the configure skeleton.
        for filename, content in self.IOC_configure_Skeleton.items():
            self.WriteFile(('configure', filename), content)

        self.TopMakefileList = ['configure']
        self.ModuleList = set()

        self.__WriteIoc()
        self.__Close()

            
    def __WriteIoc(self):
        ioc = '%s-%s-IOC-%02d' % (self.domain, self.techArea, self.id)
        self.SetIocName(ioc)

        # Create the core directories for this ioc
        iocBootDir = os.path.join('iocBoot', 'ioc' + ioc)
        iocAppDir  = ioc + 'App'
        self.MakeDirectory(iocBootDir)
        self.MakeDirectory(iocAppDir)

#         # The data path needs to be set before the database is expanded.
#         self.SetDataPath(iocBootDir)

        # Create the Db directory and its associated files.
        self.CreateDatabaseFiles(ioc, iocAppDir)

        self.CreateBootFiles(ioc, iocBootDir)

        # In static build mode create the source directory and add all the
        # modules we use to the list of libraries.
        if not configure.Configure.dynamic_load:
            self.CreateSourceFiles(ioc, iocAppDir)
            self.ModuleList.update(libversion.ModuleBase.ListModules())

        
    def __Close(self):
        '''This should be called when all IOCs have been written.  This writes
        the final version of the top level makefile and the configure RELEASE
        file needed by the makefile system.'''
        self.WriteFile('Makefile', self.TopMakefile)
        self.WriteFile('configure/RELEASE', self.ConfigureRelease)

        # If there are any data files to copy, create the data directory and
        # put them in place.
        if self.DataFileCount():
            self.MakeDirectory('data')
            self.CopyDataFiles(self.iocRoot)


    def CreateDatabaseFiles(self, ioc, iocAppDir):
        iocDbDir   = os.path.join(iocAppDir, 'Db')
        self.MakeDirectory(iocDbDir)

        # Names of the db files we're about to build
        db = ioc + '.db'
        substitutions = ioc + '.expanded.substitutions'
        expanded = ioc + '.expanded.db'

        # Generate the .db and substitutions files and compute the
        # appropriate makefile targets.
        DbTargets = []
        if self.CountRecords():
            self.AddDatabase(os.path.join('db', db))
            self.WriteFile((iocDbDir, db), self.PrintRecords, )
            DbTargets.append(db)
        if self.CountSubstitutions():
            self.WriteFile((iocDbDir, substitutions), self.PrintSubstitutions)
            self.AddDatabase(os.path.join('db', expanded))
            DbTargets.append(expanded)

        self.WriteFile((iocDbDir, 'Makefile'), self.DbMakefile, DbTargets)

        self.TopMakefileList.append(iocDbDir)

        
    def CreateSourceFiles(self, ioc, iocAppDir):
        iocSrcDir  = os.path.join(iocAppDir, 'src')
        self.MakeDirectory(iocSrcDir)
        self.WriteFile((iocSrcDir, 'Makefile'), self.SrcMakefile, ioc)
        self.TopMakefileList.append(iocSrcDir)


    def CreateBootFiles(self, ioc, iocBootDir):
        # Create the st.cmd file with appropriate hooks.
        # Start by telling iocinit which .db files to load
        if self.CountAutosaves():
            self.WriteFile(
                (iocBootDir, '0.req'), self.PrintAutosaves, header=None)
            # The autosave directory needs to be configured before writing
            # the command file.
            hardware.Autosave.SetAutosaveDir(iocBootDir)
#         # Copy any IOC specific files into the configured data directory.
#         self.CopyDataFiles(self.iocRoot)

        if self.make_boot:
            self.WriteFile(
                (iocBootDir, 'st%s.cmd' % ioc),
                self.PrintIoc, '../..', maxLineLength=126)
            self.WriteFile((iocBootDir, 'Makefile'),
                self.IOC_MAKEFILE_TEMPLATE % locals())
            self.TopMakefileList.append(iocBootDir)
        else:
            self.WriteFile((iocBootDir, 'st.cmd'), 
                self.PrintIoc, '../..', maxLineLength=126)
    

    def TopMakefile(self):
        # The top level makefile simply invokes make in all of the subsiduary
        # application directories.
        print 'TOP=.'
        print 'include $(TOP)/configure/CONFIG_APP'
        for target in self.TopMakefileList:
            print 'DIRS += %s' % target
        print 'include $(TOP)/configure/RULES_TOP'
        


    def DbMakefile(self, DbTargets):
        print 'TOP=../..'
        print 'PATH:=$(PATH):%s' % msiPath        
        print 'include $(TOP)/configure/CONFIG'
        for target in DbTargets:
            print 'DB += %s' % target
        print 'include $(TOP)/configure/RULES'


    def SrcMakefile(self, ioc):
        dbd = ioc
        print 'TOP=../..'
        print 'include $(TOP)/configure/CONFIG'
        print 'PROD_IOC = %s' % ioc
        print
        print 'DBD += %s.dbd' % dbd
        for dbd_part in Hardware.GetDbdList():
            print '%s_DBD += %s' % (dbd, dbd_part)
        print
        print '%s_SRCS += %s_registerRecordDeviceDriver.cpp' % (ioc, dbd)
        print '%s_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary' % ioc
        print

        # Library dependencies need to be expressed in reverse dependency
        # order so that each library pulls in the required symbols from the
        # next library loaded.
        for lib in reversed(Hardware.GetLibList()):
            print '%s_LIBS += %s' % (ioc, lib)
        print '%s_LIBS += $(EPICS_BASE_IOC_LIBS)' % ioc
        print
        print 'include $(TOP)/configure/RULES'
        

    def ConfigureRelease(self):
        # The epicsBase module has a rather special role in the RELEASE file:
        # it must appear, even if we're not actually linking anything, and it
        # must appear last.
        for module in sorted(self.ModuleList):
            print '%s = %s' % (module.MacroName(), module.LibPath())
