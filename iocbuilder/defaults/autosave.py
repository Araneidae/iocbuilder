# Support for autosave/restore.  This needs to be tied into record support
# for programmer suppport.

import os.path, sys
from iocbuilder import Device, Substitution, Call_TargetOS
from iocbuilder.recordbase import Record

__all__ = ['Autosave', 'SetAutosaveServer']


class _AutosaveFile(Substitution):
    Arguments = ('device', 'file',)
    TemplateFile = 'dlssrfile.template'

    
class _AutosaveStatus(Substitution):
    Arguments = ('device',)
    TemplateFile = 'dlssrstatus.template'

    
class Autosave(Device):
    LibFileList = ['autosave']
    DbdFileList = ['asSupport']

    def __init__(self, iocName, debug=0, skip_1=False):
        self.__super.__init__()

        self.autosave_dir = None
        self.__iocName = iocName
        self.__debug = debug
        self.skip_1 = skip_1

        _AutosaveFile(device = iocName, file = '0')
        _AutosaveStatus(device = iocName)

        self.autosaves = {}
        Record.AddMetadataHook(
            self.PrintMetadata, Autosave = self.AutosaveField)


    # Called during record output, we add the autosave metadata
    def PrintMetadata(self, record):
        for field in self.autosaves.get(record.name, []):
            print '#%% autosave 0 %s' % field

    # Called during record building to mark individual fields on records to
    # be autosaved.
    def AutosaveField(self, record, *fieldnames):
        '''Marks all named fields of the given record to be autosaved.'''
        fieldset = self.autosaves.setdefault(record.name, set())
        for fieldname in fieldnames:
            record.ValidFieldName(fieldname)
            fieldset.add(fieldname)


    def Initialise_vxWorks(self):
        print 'hostAdd "%s", "%s"' % (self.AutosaveServer, self.AutosaveIp)
        print 'nfsAuthUnixSet "%s", %d, %d, 0, 0' % (
            self.AutosaveServer, 37134, 500)  # gid for epics_user, pid for dcs
        print 'save_restoreSet_NFSHost "%s", "%s"' % (
            self.AutosaveServer, self.AutosavePath)
        print 'requestfilePath = malloc(256)'
        print 'sprintf requestfilePath, "%%s/%s", HOME_DIR' % \
            self.autosave_dir
        print 'set_requestfile_path requestfilePath'

    def Initialise_linux(self):
        # whatever do for mounts...
        print 'set_requestfile_path "${HOME_DIR}/"%s' % \
            quote_IOC_string(self.autosave_dir)

    def Initialise(self):
        print '# Autosave and restore initialisation'
        Call_TargetOS(self, 'Initialise')
        print 'set_savefile_path "%s/%s"' % (
            self.AutosavePath, self.__iocName)
        print
        print 'save_restoreSet_status_prefix "%s"' % self.__iocName
        print 'save_restoreSet_Debug %d' % self.__debug
        print 'save_restoreSet_NumSeqFiles 3'
        print 'save_restoreSet_SeqPeriodInSeconds 600'
        print 'save_restoreSet_DatedBackupFiles 1'
        print 'save_restoreSet_IncompleteSetsOk 1'
        print 'set_pass0_restoreFile "%s_0.sav"' % self.__iocName
        if not self.skip_1:
            print 'set_pass0_restoreFile "%s_1.sav"' % self.__iocName
            print 'set_pass1_restoreFile "%s_1.sav"' % self.__iocName
        print 'set_pass1_restoreFile "%s_2.sav"' % self.__iocName

    def PostIocInitialise(self):
        print 'create_monitor_set "%s_0.req", 5, ""' % self.__iocName
        print 'create_monitor_set "%s_1.req", 30, ""' % self.__iocName
        print 'create_monitor_set "%s_2.req", 30, ""' % self.__iocName


    def GenerateBootFiles(self, makefile, bootdir):
        if not self.autosaves:
            return
            
        self.autosave_dir = 'db'
        print >> sys.stderr, 'Need to look at this again...'
        autosave_file = bootdir.OpenFile('%s_0.req' % self.__iocName)
        for record_name in sorted(self.autosaves.keys()):
            for fieldname in self.autosaves[record_name]:
                autosave_file.write('%s.%s\n' % (record_name, fieldname))
        autosave_file.close()
        self.autosave_dir = bootdir.Path()
    

    @classmethod
    def SetAutosaveDir(cls, autosave_dir):
        cls.autosave_dir = autosave_dir

    @classmethod
    def SetAutosaveServer(cls, server, ip, path):
        cls.AutosaveServer = server
        cls.AutosaveIp = ip
        cls.AutosavePath = path

SetAutosaveServer = Autosave.SetAutosaveServer
