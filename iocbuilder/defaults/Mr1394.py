from iocbuilder import Substitution, Device

__all__ = ['Mr1394', 'Mr1394_common']


class Mr1394(Substitution, Device):
    Arguments = ('CAM', 'ID', 'C', 'PRE', 'GROUP', 'MIRROR', 'FLIP')
    TemplateFile = 'Mr1394.db'
    
    LibFileList = ['Mr1394']
    DbdFileList = ['Mr1394']
    BinFileList = ['mr1394lib', 'ex1394']

    def InitialiseOnce(self):
        print 'noconsole'
        print 'dbdcdrv_initialize'


class Mr1394_common(Substitution):
    Arguments = ('GROUP',)
    TemplateFile = 'Mr1394_common.db'
