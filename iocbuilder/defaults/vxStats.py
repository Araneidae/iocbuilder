from iocbuilder import Substitution, Device

__all__ = ['vxStats']

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=iocname
    substitution.'''

    Arguments = ('device',)
    TemplateFile = 'vxStats.template'
    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats.dbd']

    def __init__(self, iocname):
        '''Creates a vxStats expansion instance for the named ioc.'''
        # This had better delegate to Substitution, otherwise the arguments
        # are going to go astray!  Thus the class inheritance order matters.
        self.__super.__init__(device = iocname)
