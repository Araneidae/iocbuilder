from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

from iocbuilder.modules.firewireDCAM import FirewireDCAM
from iocbuilder.modules.mjpgServer import MjpgServer
from iocbuilder.modules.areaDetector import NDROI

class Camera(Substitution):    
    '''Helper class that creates a firewireDCAM camera, an mjpgServer, and an
    ROI to join them together'''

    def __init__(self, P, PORT_PREFIX, ID, HOST, name = '', WWWPORT = 8080, 
            COLOUR = 0, SIZE = 786432, TIMEOUT = 1):
        # make an instance of firewireDCAM
        MEMORY = SIZE * 14, # 2 for driver, 2 for ROI, 1 for mjpgServer
        R = ":CAM"
        PORT = PORT_PREFIX
        FirewireDCAM(**filter_dict(locals(), FirewireDCAM.ArgInfo.Names()))
        # initialise the ROI class
        MEMORY = SIZE * 9 # 1 for mjpgServer for each ROI
        PORT = PORT_PREFIX + 'ROI'
        NDARRAY_PORT = PORT_PREFIX
        R = ':ROI'
        NDROI(**filter_dict(locals(), NDROI.ArgInfo.Names()))
        # make an instance of mjpgServer
        PORT = PORT_PREFIX + "MJPG"
        NDARRAY_PORT = PORT_PREFIX + "ROI"      
        MEMORY = SIZE # Just 1 for mjpgServer
        R = ':MJPG'
        MjpgServer(**filter_dict(locals(), MjpgServer.ArgInfo.Names()))   
        # Finally, initialise self
        self.__super.__init__(P = P, name = name)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P           = Simple('Device Prefix', str),
        PORT_PREFIX = Simple('Asyn Port Name Prefix', str),
        ID          = Simple('Cam ID with 0x prefix', str),
        HOST        = Simple('Machine hosting ttp port for mjpgServer', str),
        name        = Simple('Object name', str))        
        WWWPORT     = Simple('Http port for mjpgServer', int),
        COLOUR      = Enum  ('Colour mode', ('B+W', 'Colour')),
        SIZE        = Simple('Max picture size (for memory allocation)', int),
        TIMEOUT     = Simple('Timeout', int))

    # Substitution attributes
    Arguments = ['P', 'name']
    TemplateFile = 'camera.db'

