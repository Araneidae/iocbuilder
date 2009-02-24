from iocbuilder import Substitution, Device

__all__ = ['vxStats']

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=device
    substitution.'''
    # __init__ arguments
    ArgInfo = [('device', str, 'Device Prefix')]
    # Substitution attributes
    TemplateFile = 'vxStats.template'
    # Device attributes    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats']
