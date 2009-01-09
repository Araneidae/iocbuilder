from iocbuilder import Substitution, Device
from iocbuilder.hardware import genSub

__all__ = [
    'BL_EVR_PMC', 'decode', 'event_stats',
    'evr_alive', 'evr_usec_calc', 'offset']


class BL_EVR_PMC(Substitution):
    Arguments = ('device', 'card')
    TemplateFile = 'BL-EVR-PMC.template'

class decode(Substitution):
    Arguments = ('DEVICE', 'DEVIEC', 'EVENT', 'NAME')
    TemplateFile = 'decode.template'
    # Ooops: nasty typo in template!

class event_stats(Substitution, Device):
    Arguments = ('SYSTEM', 'EVNAME', 'EVNUM')
    TemplateFile = 'event_stats.template'

    Dependencies = (genSub,)
    LibFileList = ['timingfuncs']
    DbdFileList = ['TimingTemplates.dbd']

class evr_alive(Substitution):
    Arguments = ('SYSTEM', 'EVENT')
    TemplateFile = 'evr_alive.template'

class evr_usec_calc(Substitution):
    Arguments = ('SYSTEM', 'CHANNEL', 'DEFAULT', 'GROUP', 'GUIMAX', 'GUIMIN')
    TemplateFile = 'evr_usec_calc.template'

class offset(Substitution):
    Arguments = ('SYSTEM', 'LOPR', 'HOPR')
    TemplateFile = 'offset.template'
