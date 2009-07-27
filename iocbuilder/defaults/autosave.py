# Support for autosave/restore.  This needs to be tied into record support
# for programmer suppport.

import os.path, sys
from iocbuilder import Device, Substitution, Call_TargetOS
from iocbuilder.recordbase import Record
from iocbuilder import iocwriter


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

        self.autosave_dir = 'data'
        self.__iocName = iocName
        self.__debug = debug
        self.skip_1 = skip_1
        self.__rule_added = False
        self.__db_names = []

        _AutosaveFile(device = iocName, file = '0')
        _AutosaveStatus(device = iocName)

        self.autosaves = {}
        Record.AddMetadataHook(
            self.PrintMetadata, Autosave = self.AutosaveField)

        iocwriter.AutoSaveDatabaseHook = self.AddDatabase


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
        for db_name in self.__db_names:
            print 'set_pass0_restoreFile "%s_0.sav"' % db_name
            if not self.skip_1:
                print 'set_pass0_restoreFile "%s_1.sav"' % db_name
                print 'set_pass1_restoreFile "%s_1.sav"' % db_name
            print 'set_pass1_restoreFile "%s_2.sav"' % db_name


    def PostIocInitialise(self):
        for db_name in self.__db_names:
            print 'create_monitor_set "%s_0.req",  5, ""' % db_name
            print 'create_monitor_set "%s_1.req", 30, ""' % db_name
            print 'create_monitor_set "%s_2.req", 30, ""' % db_name


    def AddDatabase(self, db_name, makefile, own_records):
        if own_records and not self.autosaves:
            # No autosaves in this db file
            return
        
        # Called when a .db file is added
        if not self.__rule_added:
            self.__rule_added = True
            makefile.AddRule(_REQ_DB_RULE)

        self.__db_names.append(db_name)
        for n in range(3):
            makefile.AddLine('DATA += %s_%d.req' % (db_name, n))
            
    
    @classmethod
    def SetAutosaveServer(cls, server, ip, path):
        cls.AutosaveServer = server
        cls.AutosaveIp = ip
        cls.AutosavePath = path

SetAutosaveServer = Autosave.SetAutosaveServer

# Rule to build all three .req files by postprocessing the corresponding .db
# file.
_REQ_DB_RULE = '''
%_1.req %_2.req %_0.req: %.db
\t/dls_sw/tools/bin/epicsparser.py -s as -r $* $^
\ttouch $*_0.req $*_1.req $*_2.req
'''
