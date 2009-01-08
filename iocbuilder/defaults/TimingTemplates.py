from iocbuilder import Substitution, Device, GetDevice, UnsetDevice
from iocbuilder.hardware import genSub

__all__ = ['MonitorEvent', 'EvrAlive']


# Templates for event statistics

class MonitorEvent(Substitution, Device):
    # Template arguments:
    #   SYSTEM      Device name to use here.
    #   EVNAME      Name of event being monitored
    #   EVNUM       Number of event being monitored
    Arguments = ('SYSTEM', 'EVNAME', 'EVNUM')
    TemplateFile = 'event_stats.template'

    Dependencies = (genSub,)
    LibFileList = ['timingfuncs']
    DbdFileList = ['TimingTemplates.dbd']


    # "Official" event names as defined by Angelos
    _EventNames = {
        0x20: 'TZERO',      0x21: 'LB0DITRG',
        0x24: 'LINACPRE',   0x25: 'LINACHBT',
        0x26: 'LBDITRG',    0x2A: 'BRHWTRG',
        0x2C: 'BRINJ',      0x30: 'BRPREXTR',
        0x31: 'BSDITRG',    0x32: 'SRPREINJ',
        0x3C: 'SRINJ',      0x40: 'SRDITRG',
        0x53: 'TOPUPON',    0x54: 'TOPUPOFF',
        0x5D: 'BEAMLOSS',   0x5E: 'MPSTRIP',
        0x7D: 'TSRESET' }        

    def __init__(self, eventMap, **kargs):
        '''Monitors the event receiver event specified by eventMap. 
        '''
        evnum = eventMap.SoftEvent(**kargs).event
        eventMap.er.SetDevice()
        self.__super.__init__(
            SYSTEM = GetDevice(),
            EVNAME = self._EventNames[evnum],
            EVNUM  = evnum)
        UnsetDevice()

        
class EvrAlive(Substitution):
    # Template arguments:
    #   SYSTEM      Device name
    #   EVENT       Event number to use for monitor
    Arguments = ('SYSTEM', 'EVENT')
    TemplateFile = 'evr_alive.template'


    def __init__(self, er, **kargs):
        # Ensure that we receive a Linac heartbeat soft event.
        self.softEvent = \
            er.EventMap('LINAC-HBT', er.LINAC_HBT).SoftEvent(**kargs)
        er.SetDevice()
        self.__super.__init__(
            SYSTEM = GetDevice(),
            EVENT  = self.softEvent.event)
        UnsetDevice()
