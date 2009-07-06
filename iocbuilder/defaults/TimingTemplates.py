from iocbuilder import Substitution, Device, GetDevice, UnsetDevice
from iocbuilder.modules.genSub import genSub

__all__ = ['MonitorEvent', 'EvrAlive']


# Depends on EventReceiver (er, erevent)
class BL_EVR_PMC(Substitution):
    Arguments = ('device', 'card')
    TemplateFile = 'BL-EVR-PMC.template'

# Depends on EventReceiver (erevent)
class decode(Substitution):
    Arguments = ('DEVICE', 'DEVIEC', 'EVENT', 'NAME')
    TemplateFile = 'decode.template'
    # Ooops: nasty typo in template!

# Depends on genSub
class event_stats(Substitution, Device):
    Arguments = ('SYSTEM', 'EVNAME', 'EVNUM')
    TemplateFile = 'event_stats.template'

    Dependencies = (genSub,)
    LibFileList = ['timingfuncs']
    DbdFileList = ['TimingTemplates']

class evr_alive(Substitution):
    Arguments = ('SYSTEM', 'EVENT')
    TemplateFile = 'evr_alive.template'

class evr_usec_calc(Substitution):
    Arguments = ('SYSTEM', 'CHANNEL', 'DEFAULT', 'GROUP', 'GUIMAX', 'GUIMIN')
    TemplateFile = 'evr_usec_calc.template'

class offset(Substitution):
    Arguments = ('SYSTEM', 'LOPR', 'HOPR')
    TemplateFile = 'offset.template'


# Templates for event statistics

def MonitorEvent(eventMap, **kargs):
    '''Monitors the event receiver event specified by eventMap. 
    '''
    # "Official" event names as defined by Angelos
    EventNames = {
        0x20: 'TZERO',      0x21: 'LB0DITRG',
        0x24: 'LINACPRE',   0x25: 'LINACHBT',
        0x26: 'LBDITRG',    0x2A: 'BRHWTRG',
        0x2C: 'BRINJ',      0x30: 'BRPREXTR',
        0x31: 'BSDITRG',    0x32: 'SRPREINJ',
        0x3C: 'SRINJ',      0x40: 'SRDITRG',
        0x53: 'TOPUPON',    0x54: 'TOPUPOFF',
        0x5D: 'BEAMLOSS',   0x5E: 'MPSTRIP',
        0x7D: 'TSRESET' }

    evnum = eventMap.SoftEvent(**kargs).event
    return event_stats(
        SYSTEM = eventMap.er.GetDevice(),
        EVNAME = EventNames[evnum],
        EVNUM  = evnum)

        
class EvrAlive(evr_alive):
    def __init__(self, er, **kargs):
        # Ensure that we receive a Linac heartbeat soft event.
        self.softEvent = \
            er.EventMap('LINAC-HBT', er.LINAC_HBT).SoftEvent(**kargs)
        self.__super.__init__(
            SYSTEM = er.GetDevice(),
            EVENT  = self.softEvent.event)
