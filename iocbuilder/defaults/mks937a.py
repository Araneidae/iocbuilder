from iocbuilder import Substitution
from iocbuilder.hardware import AutoProtocol
from iocbuilder.validators import TwoDigitInt, asynPort

class _ProtocolBase(Substitution, AutoProtocol):
    ProtocolFiles = ['mks937a.protocol']

class mks937aTemplate(_ProtocolBase):
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', asynPort, 'Asyn Serial Port')
    ]
    XMLObjects = ['port']    
    # Substitution attributes
    TemplateFile = 'mks937a.template'

class mks937aTemplate_sim(mks937aTemplate):
    XMLObjects = []
    TemplateFile = 'simulation_mks937a.template'
mks937aTemplate_sim.ArgInfo[1]=('port', str, 'Dummy Asyn Serial Port')    

class mks937aImgTemplate(_ProtocolBase):
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('controller', None, 'mks937aTemplate instance'),
        ('channel', int, 'Channel number, normally 1 or 2')
    ]
    XMLObjects = ['controller']    
    IdenticalSim = True    
    # Substitution attributes
    TemplateFile = 'mks937aImg.template'
    Arguments = ('device','port','channel')    
    # get the port from mks937aTemplate, then init        
    def __init__(self, controller, **kwargs):
        self.__super.__init__(port = controller.args['port'], **kwargs)

class mks937aPirgTemplate(mks937aImgTemplate):
    # Substitution attributes
    TemplateFile = 'mks937aPirg.template'
    ArgInfo = mks937aImgTemplate.ArgInfo
    ArgInfo[2]=(
        'channel', int, 'Channel number, normally 4 or 5')    
            
class mks937aGaugeTemplate(Substitution):
    # __init__ arguments
    ArgInfo = [
        ('dom', str, 'Domain, e.g. BLXXI'),
        ('id', TwoDigitInt, 'ID e.g. 1'),
        ('cs', int, 'Card number, e.g. 40'),
        ('s', int, 'Signal number, e.g. 0')
    ]
    # Substitution attributes    
    TemplateFile = 'mks937aGauge.template'
    
class mks937aGaugeTemplate_sim(mks937aGaugeTemplate):
    TemplateFile = 'simulation_mks937aGauge.template'

class mks937aGaugeGroupTemplate(Substitution):
    Arguments = (
        'device',
        'gauge1', 'gauge2', 'gauge3', 'gauge4',
        'gauge5', 'gauge6', 'gauge7', 'gauge8')
    TemplateFile = 'mks937aGaugeGroup.template'
    IdenticalSim = True  

class mks937aImgGroupTemplate(Substitution):
    Arguments = (
        'device',
        'img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8')
    TemplateFile = 'mks937aImgGroup.template'
    IdenticalSim = True  

class mks937aPirgGroupTemplate(Substitution):
    Arguments = (
        'device',
        'pirg1', 'pirg2', 'pirg3', 'pirg4',
        'pirg5', 'pirg6', 'pirg7', 'pirg8')
    TemplateFile = 'mks937aPirgGroup.template'
    IdenticalSim = True  

class mks937aImgDummyTemplate(Substitution):
    Arguments = ('device',)
    TemplateFile = 'mks937aImgDummy.template'
    IdenticalSim = True  
