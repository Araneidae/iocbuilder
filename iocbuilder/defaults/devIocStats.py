from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

class ioc(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''
    # __init__ arguments
    ArgInfo = makeArgInfo(
        IOCNAME = Simple('IOC name', str))
    
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'ioc.db'
    
    # Device attributes    
    LibFileList = ['devIocStats']
    DbdFileList = ['iocAdmin']
    
#    IdenticalSim = True    
#    EdmScreen = ('ioc_stats.edl','ioc=%(IOCNAME)s')
#    EdmEmbedded = ('ioc_embed.edl','ioc=%(IOCNAME)s')
#    SevrPv = '%(IOCNAME)s:LOAD'