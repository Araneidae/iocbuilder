from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

__all__ = ['vxStats']

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''

    # __init__ attributes
    ArgInfo = makeArgInfo(device = Simple('Device Prefix', str))
        
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'vxStats.template'
    
    # Device attributes    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats']


