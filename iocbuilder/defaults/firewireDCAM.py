from iocbuilder import Device, Substitution, SetSimulation
from iocbuilder.arginfo import *

from iocbuilder.modules.areaDetector import AreaDetector, ADBase, simDetector
from iocbuilder.modules.dc1394 import Dc1394

class FirewireDCAM(Substitution, Device):
    '''Creates a firewire camera'''
    Dependencies = (AreaDetector, Dc1394)
    
    # work out with args are for firewireDCAM.db, and which are for ADBase
    def __init__(self,
            ID, MEMORY, BUFFERS = 16, SPEED = 800, COLOUR = 0, **args):     
        CAM = args["R"].rstrip(":")
        locals().update(args)        
        R = CAM+":"
        self.__dict__.update(locals())
        ADBase(**filter_dict(locals(), ADBase.ArgInfo.Names()))
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = ADBase.ArgInfo + makeArgInfo(__init__,
        ID     = Simple('Cam ID with 0x prefix', str),
        MEMORY = Simple(
            'Max memory to allocate, should be maxw*maxh*nbuffer for driver'
            ' and all attached plugins', int),        
        BUFFERS = Simple(
            'Maximum number of NDArray buffers to be created for plugin'
            ' callbacks', int),        
        SPEED  = Choice('Bus speed', [400, 800]),
        COLOUR = Enum  ('Colour mode', ['B+W', 'Col'])) 

    # Device attributes
    LibFileList = ['firewireDCAM']
    DbdFileList = ['firewireDCAM']    

    # Substitution attributes
    Arguments = ("P","CAM","PORT")
    TemplateFile = 'firewireDCAM.db'

    def InitialiseOnce(self):
        print '# Scan the firewire bus for cameras'
        print 'FDC_InitBus()'

    def Initialise(self):
        # ADBase has stored these for us
        print 'FDC_Config("%(PORT)s", %(ID)s, %(SPEED)d, %(BUFFERS)d,' \
            ' %(MEMORY)d, %(COLOUR)d)' % self.__dict__

# just use a simDetector for simulations
def FirewireDCAM_sim(**args):
    return simDetector(
        WIDTH = 1024, HEIGHT = 768,
        **filter_dict(args, simDetector.ArgInfo.Names()))
SetSimulation(FirewireDCAM, FirewireDCAM_sim)
