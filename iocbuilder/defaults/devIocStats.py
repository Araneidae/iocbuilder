from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

class ioc(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''
    # __init__ arguments
    ArgInfo = makeArgInfo(
        IOCNAME = Simple('IOC name', str),
        name    = Simple('Object name', str))
    
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'ioc.db'
    
    # Device attributes    
    LibFileList = ['devIocStats']
    DbdFileList = ['iocAdmin']
