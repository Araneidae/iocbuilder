from iocbuilder import Device, Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.areaDetector import AreaDetector, ADBase
from iocbuilder.modules.dc1394 import Dc1394

__all__ = ['FirewireDCAM']

class FirewireDCAM(Substitution, Device):
    '''Creates a firewire camera'''
    Dependencies = (AreaDetector, Dc1394)
    
    # work out with args are for firewireDCAM.db, and which are for ADBase
    def __init__(self, ID, SPEED = 800, COLOUR = 0, **args):
        CAM = args["R"].rstrip(":")
        args["R"] = CAM+":"
        ADBase(**args)
        self.__dict__.update(args)
        self.ID = ID
        self.SPEED = SPEED
        self.COLOUR = COLOUR
        self.__super.__init__(P = args['P'], CAM = CAM, PORT = args["PORT"])

    # __init__ arguments
    ArgInfo = ADBase.ArgInfo + makeArgInfo(__init__,
        ID     = Simple('Cam ID with 0x prefix', str),
        SPEED  = Choice('Bus speed', [400, 800]),
        COLOUR = Enum  ('Colour mode', ['B+W', 'Col']))

    # Substitution attributes
    Arguments = ("P","CAM","PORT")
    TemplateFile = 'firewireDCAM.db'    

    # Device attributes
    LibFileList = ['firewireDCAM']
    DbdFileList = ['firewireDCAM']    

    def InitialiseOnce(self):
        print '# Scan the firewire bus for cameras'
        print 'FDC_InitBus()'

    def Initialise(self):
        print 'FDC_Config("%(PORT)s", %(ID)s, %(SPEED)d, %(BUFFERS)d, %(MEMORY)d, %(COLOUR)d)'%self.__dict__
