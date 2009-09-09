from iocbuilder import Substitution, SetSimulation
from iocbuilder.modules.streamDevice import AutoProtocol
from iocbuilder.modules.asyn import AsynPort
from iocbuilder.arginfo import *


class mks937a(Substitution, AutoProtocol):    
    '''MKS 937a Gauge controller for IMGs and PIRGs'''

    # __init__ attributes
    ArgInfo = makeArgInfo(
        device = Simple('Device Prefix', str),
        port   = Ident ('Asyn Serial Port', AsynPort))

    # Substitution attributes
    TemplateFile = 'mks937a.template'        
    Arguments = ArgInfo.Names()
    
    # AutoProtocol attributes
    ProtocolFiles = ['mks937a.protocol']    

# The simulation has a slightly different db file                      
class mks937a_sim(mks937a):
    TemplateFile = 'simulation_mks937a.template'    
SetSimulation(mks937a, mks937a_sim)     


class mks937aImg(Substitution):
    '''Template for controlling an IMG attached to an MKS 937a'''
    
    # get the port from mks937a, then init        
    def __init__(self, device, controller, channel, name = ''):
        port = controller.args['port']
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ attributes
    ArgInfo = makeArgInfo(__init__, 
        device     = Simple('Device Prefix', str),
        controller = Ident ('Parent mks937a instance', mks937a),
        channel    = Simple('Channel number', int),
        name       = Simple('Object name', str))        

    # Substitution attributes
    Arguments = ArgInfo.Names(without = 'controller') + ['port']
    TemplateFile = 'mks937aImg.template'

      
class mks937aPirg(mks937aImg):
    '''Template for controlling a PIRG attached to an MKS 937a'''
    
    # This is almost identical to the Img, just a different template
    # Substitution attributes
    TemplateFile = 'mks937aPirg.template'


try:
    # try to make some simulations, but need pressArr
    from iocbuilder.modules.pressArr_subrec import pressArr
    
    class mks937aImg_sim(mks937aImg):
        Dependencies = (pressArr,)
        TemplateFile = 'simulation_mks937aImg.template'
        
    SetSimulation(mks937aImg, mks937aImg_sim)         

    class mks937aPirg_sim(mks937aPirg):
        Dependencies = (pressArr,)
        TemplateFile = 'simulation_mks937aPirg.template'
        
    SetSimulation(mks937aPirg, mks937aPirg_sim)         

except ImportError:
    print "# pressarr not included, cannot make mks937a simulations"

                                                                                                            
class mks937aGauge(Substitution):
    '''Template for reading the analogue pressure from an MKS 937a'''

    # Make sure the id is formatted correctly, then init
    def __init__(self, dom, id, c, s):
        id = "%02d" % id
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ attributes
    ArgInfo = makeArgInfo(__init__,
        dom = Simple('Domain, e.g. BLXXI', str),
        id  = Simple('ID e.g. 1', int),
        c   = Simple('Card number, e.g. 40', int),
        s   = Simple('Signal number, e.g. 0', int))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'mks937aGauge.template'    

# The simulation has a slightly different db file
class mks937aGauge_sim(mks937aGauge):
    TemplateFile = 'simulation_mks937aGauge.template'
SetSimulation(mks937aGauge, mks937aGauge_sim)    


class mks937aGaugeGroup(Substitution):
    Arguments = (
        'device',
        'gauge1', 'gauge2', 'gauge3', 'gauge4',
        'gauge5', 'gauge6', 'gauge7', 'gauge8')
    TemplateFile = 'mks937aGaugeGroup.template'


class mks937aImgGroup(Substitution):
    Arguments = (
        'device',
        'img1', 'img2', 'img3', 'img4', 'img5', 'img6', 'img7', 'img8')
    TemplateFile = 'mks937aImgGroup.template'


class mks937aPirgGroup(Substitution):
    Arguments = (
        'device',
        'pirg1', 'pirg2', 'pirg3', 'pirg4',
        'pirg5', 'pirg6', 'pirg7', 'pirg8')
    TemplateFile = 'mks937aPirgGroup.template'


class mks937aImgDummy(Substitution):
    Arguments = ('device',)
    TemplateFile = 'mks937aImgDummy.template'

