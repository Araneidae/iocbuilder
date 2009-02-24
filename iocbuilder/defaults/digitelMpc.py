from iocbuilder import Substitution
from iocbuilder.hardware import AutoProtocol
from iocbuilder.validators import TwoDigitInt, asynPort

class _digitelBase(Substitution, AutoProtocol):
    ProtocolFiles = ['digitelMpc.proto']

class digitelMpcTemplate(_digitelBase):
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', asynPort, 'Asyn Serial Port'),
        ('unit', TwoDigitInt, 'Unit number (for multidrop serial)', 1)
    ]
    XMLObjects = ['port']    
    # Substitution attributes
    TemplateFile = 'digitelMpc.template'

class digitelMpcTemplate_sim(digitelMpcTemplate):
    TemplateFile = 'simulation_digitelMpc.template'
    XMLObjects = []    
digitelMpcTemplate_sim.ArgInfo[1]=('port', str, 'Dummy Asyn Serial Port')

class digitelMpcTspTemplate(_digitelBase):
    Arguments = ('device', 'port' , 'unit' , 'ctlsrc')
    TemplateFile = 'digitelMpcTsp.template'
    IdenticalSim = True

class digitelMpcIonpTemplate(_digitelBase):
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('MPC', None, 'digitelMPC object'),
        ('pump', int, 'Pump number'),
        ('size', int, 'Pump size (l)'),
        ('spon', int, 'Setpoint for on', 0),
        ('spoff', int, 'Setpoint for off', 0)
    ]
    XMLObjects = ['MPC']    
    # Substitution attributes
    Arguments = ['device', 'port', 'unit'] + [x[0] for x in ArgInfo[2:]]
    TemplateFile = 'digitelMpcIonp.template'
    IdenticalSim = True
    # get the device, port and unit from MPC object, then init        
    def __init__(self, MPC, **kwargs):
        self.__super.__init__(port = MPC.args['port'], 
            unit = MPC.args['unit'], **kwargs)
    
class digitelMpcIonpGroupTemplate(Substitution):
    Arguments = (
        'device', 'delay',
        'ionp1', 'ionp2', 'ionp3', 'ionp4',
        'ionp5', 'ionp6', 'ionp7', 'ionp8')
    TemplateFile = 'digitelMpcIonpGroup.template'
    IdenticalSim = True    

class digitelMpcTspGroupTemplate(Substitution):
    Arguments = (
        'device',
        'tsp1', 'tsp2', 'tsp3', 'tsp4', 'tsp5', 'tsp6', 'tsp7', 'tsp8')
    TemplateFile = 'digitelMpcTspGroup.template'
    IdenticalSim = True

class dummyIonpTemplate(Substitution):
    Arguments = ('device',)
    TemplateFile = 'dummyIonp.template'
    IdenticalSim = True
