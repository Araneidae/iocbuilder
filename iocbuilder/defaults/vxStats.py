from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

__all__ = ['vxStats']

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''

    # Device attributes    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats']

    def __init__(self, device):
        self.__super.__init__(device = device)

    # __init__ attributes
    ArgInfo = makeArgInfo(__init__,
        device = Simple('Device Prefix', str))

    # Substitution attributes
    TemplateFile = 'vxStats.template'
    Arguments = ArgInfo.Names()
