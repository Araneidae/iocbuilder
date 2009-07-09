# Support for autosave/restore.  This needs to be tied into record support
# for programmer suppport.

import os.path
from iocbuilder import Device, Substitution
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

    def __init__(self, iocName, debug=0):
        self.__super.__init__()

        Autosave.autosave_dir = None
        self.__iocName = iocName
        self.__debug = debug

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


    def Initialise(self):
        print '# Autosave and restore initialisation'
        print 'hostAdd "%s", "%s"' % (self.AutosaveServer, self.AutosaveIp)
        print 'nfsAuthUnixSet "%s", %d, %d, 0, 0' % (
            self.AutosaveServer, 1015, 500)  # gid for mga83, pid for dcs
        print 'nfsMount "%s", "%s", "/autosave"' % (
            self.AutosaveServer, self.AutosavePath)
        print
        print 'save_restoreSet_status_prefix "%s"' % self.__iocName
        print 'save_restoreSet_Debug %d' % self.__debug
        print 'save_restoreSet_NumSeqFiles 0'
        print 'save_restoreDatedBackupFiles=0'
        print 'set_pass0_restoreFile "0.sav"'
        print 'set_pass1_restoreFile "0.sav"'
        
        if self.autosave_dir:
            print 'requestfilePath = malloc(256)'
            print 'sprintf requestfilePath, "%%s/%s", HOME_DIR' % \
                self.autosave_dir
            print 'set_requestfile_path requestfilePath'
        else:
            print 'set_requestfile_path HOME_DIR'

        print 'set_savefile_path "/autosave/%s"' % self.__iocName

    def PostIocInitialise(self):
        req_file = '0.req'
        print 'create_monitor_set "%s", 10, ""' % req_file


    def GenerateBootFiles(self, makefile, bootdir):
        if not self.autosaves:
            return
            
        autosave_file = bootdir.OpenFile('0.req')
        for record_name in sorted(self.autosaves.keys()):
            for fieldname in self.autosaves[record_name]:
                autosave_file.write('%s.%s\n' % (record_name, fieldname))
        autosave_file.close()
        Autosave.autosave_dir = bootdir.Path()
    

    @classmethod
    def SetAutosaveDir(cls, autosave_dir):
        cls.autosave_dir = autosave_dir

    @classmethod
    def SetAutosaveServer(cls, server, ip, path):
        cls.AutosaveServer = server
        cls.AutosaveIp = ip
        cls.AutosavePath = path

SetAutosaveServer = Autosave.SetAutosaveServer
