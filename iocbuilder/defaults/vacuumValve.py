from iocbuilder import Substitution, ModuleBase
from iocbuilder.hardware import HostLink
from iocbuilder.validators import TwoDigitInt, asynPort

class vacuumValveReadTemplate(Substitution):
    Dependencies = (HostLink,)
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', asynPort, 'Asyn Serial Port'),
    ]
    XMLObjects = ['port']    
    # Substitution attributes
    TemplateFile = 'vacuumValveRead.template'   

class vacuumValveReadTemplate_sim(ModuleBase):
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', str, 'Dummy Asyn Serial Port'),
    ]    
    def __init__(self,**args):
        self.args = args

class vacuumValve_callbackTemplate(Substitution):
    Dependencies = (HostLink,)
    # __init__ arguments
    ArgInfo = [ 
        ('device', str, 'Device Prefix'),
        ('crate', None, 'vacuumValveReadTemplate object'),
        ('valve', TwoDigitInt, 'Valve number (1 to 6) in PLC'),
        ('gda_name', str, 'GDA short name', ''),
        ('gda_desc', str, 'GDA description', '') ] +\
        [('ilk%s'%i, str, 'Interlock %s Description'%i, '') 
            for i in range(16) ] +\
        [('ilk%s'%i, str, 'Gauge Interlock %s Description'%i, '') 
            for i in range(16) ]  
    XMLObjects = ['crate']                     
    # Substitution attributes  
    Arguments = ['device','vlvcc','port'] + [x[0] for x in ArgInfo[2:]]
    TemplateFile = 'vacuumValve_callback.template'
    # get the device and port from the vacuumValveReadTemplate object, then
    # init 
    def __init__(self,crate,**kwargs):
        self.__super.__init__(port = crate.args['port'], 
            vlvcc = crate.args['device'], **kwargs)

class vacuumValve_callbackTemplate_sim(vacuumValve_callbackTemplate):
    Dependencies = ()
    TemplateFile = 'simulation_vacuumValve.template'

class externalValve(ModuleBase):
    '''Empty class that looks like a valve, allowing linking to FE valves'''
    ArgInfo = [
        ('device', str, 'Device Prefix')
    ]
    IdenticalSim = True
    def __init__(self,**args):
        self.args = args

class vacuumValveGroupTemplate(Substitution):
    Arguments = (
        'device', 'delay',
        'valve1', 'valve2', 'valve3', 'valve4',
        'valve5', 'valve6', 'valve7', 'valve8')
    TemplateFile = 'vacuumValveGroup.template'
    IdenticalSim = True  

class dummyValveTemplate(Substitution):
    Arguments = ('device',)
    TemplateFile = 'dummyValve.template'
    IdenticalSim = True  
