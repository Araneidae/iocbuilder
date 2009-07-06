from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.streamDevice import AutoProtocol
from iocbuilder.modules.asyn import AsynOctetInterface

class digitelMpc(Substitution, AutoProtocol):
    '''Digitel MPC Ion pump controller'''

    # Make sure unit is a 2 digit int
    def __init__(self, device, port, unit = 1):
        unit = "%02d" % unit
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        device = Simple('Device Prefix', str),
        port   = Ident ('Asyn Serial Port', AsynOctetInterface),
        unit   = Simple('Unit number (for multidrop serial)', int))

    # Substitution attributes
    TemplateFile = 'digitelMpc.template'
    Arguments = ArgInfo.Names()
    
    # AutoProtocol attributes
    ProtocolFiles = ['digitelMpc.proto']    

'''
class digitelMpc_sim(Substitution):
    TemplateFile = 'simulation_digitelMpc.template'
    XMLObjects = []
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', str, 'Dummy Asyn Serial Port'),
        ('unit', TwoDigitInt, 'Unit number (for multidrop serial)', 1)
    ]
'''

class digitelMpcPump(Substitution):
    pass
        
class digitelMpcTsp(digitelMpcPump):
    Arguments = ('device', 'port' , 'unit' , 'ctlsrc')
    TemplateFile = 'digitelMpcTsp.template'
#    IdenticalSim = True

class digitelMpcIonp(digitelMpcPump):
    '''Digitel MPC Ion pump template'''

    # Just pass the arguments straight through
    def __init__(self, device, MPC, pump, size, spon = 0, spoff = 0):
        port = MPC.args['port']
        unit = MPC.args['unit']
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        device = Simple('Device Prefix', str),
        MPC    = Ident ('digitelMPC object', digitelMpc),
        pump   = Simple('Pump number', int),
        size   = Simple('Pump size (l)', int),
        spon   = Simple('Setpoint for on', int),
        spoff  = Simple('Setpoint for off', int))

    # Substitution attributes
    Arguments = ['port', 'unit'] + ArgInfo.Names(without = ['MPC'])
    TemplateFile = 'digitelMpcIonp.template'
    
#    EdmScreen = ('digitelMpcIonpControl','device=%(device)s')

'''
class digitelMpcIonp_sim(digitelMpcIonp):
    TemplateFile = 'simulation_digitelMpcIonp.template'
'''
            
class digitelMpcIonpGroup(Substitution):
    Arguments = (
        'device', 'delay',
        'ionp1', 'ionp2', 'ionp3', 'ionp4',
        'ionp5', 'ionp6', 'ionp7', 'ionp8')
    TemplateFile = 'digitelMpcIonpGroup.template'
#    IdenticalSim = True    

class digitelMpcTspGroup(Substitution):
    Arguments = (
        'device',
        'tsp1', 'tsp2', 'tsp3', 'tsp4', 'tsp5', 'tsp6', 'tsp7', 'tsp8')
    TemplateFile = 'digitelMpcTspGroup.template'
#    IdenticalSim = True

class dummyIonp(Substitution):
    Arguments = ('device',)
    TemplateFile = 'dummyIonp.template'
#    IdenticalSim = True
