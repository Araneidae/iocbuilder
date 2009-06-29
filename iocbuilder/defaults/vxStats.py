from iocbuilder import Substitution, Device, makeArgInfo

__all__ = ['vxStats']

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''

    Arguments = ('device',)
    # Substitution attributes
    TemplateFile = 'vxStats.template'
    # Device attributes    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats']

    def __init__(self, iocname):
        self.__super.__init__(device = iocname)
    ArgInfo = makeArgInfo(__init__, iocname = (str, 'Device Prefix'))
