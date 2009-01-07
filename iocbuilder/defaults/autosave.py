# Support for autosave/restore.  This needs to be tied into record support
# for programmer suppport.

import os.path
from iocbuilder import Device, Substitution

__all__ = ['Autosave', 'SetAutosaveServer']


def SetAutosaveServer(server, ip, path):
    global _AutosaveServer, _AutosaveIp, _AutosavePath
    _AutosaveServer = server
    _AutosaveIp = ip
    _AutosavePath = path


class _AutosaveFile(Substitution):
    ModuleName = 'autosave'
    Arguments = ('device', 'file',)
    TemplateFile = 'dlssrfile.template'

    
class _AutosaveStatus(Substitution):
    ModuleName = 'autosave'
    Arguments = ('device',)
    TemplateFile = 'dlssrstatus.template'

    
class Autosave(Device):
    ModuleName = 'autosave'

    LibFileList = ['autosave']
    DbdFileList = ['asSupport.dbd']

    def __init__(self, iocName, debug=0):
        self.__super.__init__()

        Autosave.autosave_dir = None
        self.__iocName = iocName
        self.__debug = debug

        _AutosaveFile(device = iocName, file = '0')
        _AutosaveStatus(device = iocName)


    def Initialise(self):
        print '# Autosave and restore initialisation'
        print 'hostAdd "%s", "%s"' % (_AutosaveServer, _AutosaveIp)
        print 'nfsAuthUnixSet "%s", %d, %d, 0, 0' % (
            _AutosaveServer, 1015, 500)  # gid for mga83, pid for dcs
        print 'nfsMount "%s", "%s", "/autosave"' % (
            _AutosaveServer, _AutosavePath)
        print
        print 'save_restoreSet_status_prefix "%s"' % self.__iocName
        print 'save_restoreSet_Debug %d' % self.__debug
        print 'save_restoreSet_NumSeqFiles 0'
        print 'save_restoreDatedBackupFiles=0'
        print 'set_pass0_restoreFile "0.sav"'
        print 'set_pass1_restoreFile "0.sav"'
        
        if self.autosave_dir:
            print 'requestfilePath = malloc(256)'
            print 'sprintf requestfilePath, "%%s/%s", homeDir' % \
                self.autosave_dir
            print 'set_requestfile_path requestfilePath'
        else:
            print 'set_requestfile_path homeDir'

        print 'set_savefile_path "/autosave/%s"' % self.__iocName

    def PostIocInitialise(self):
        req_file = '0.req'
        print 'create_monitor_set "%s", 10, ""' % req_file

    @classmethod
    def SetAutosaveDir(cls, autosave_dir):
        cls.autosave_dir = autosave_dir
