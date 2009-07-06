from iocbuilder import Device, Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.areaDetector import AreaDetector, NDPluginBase

class MjpgServer(Substitution, Device):
    Dependencies = (AreaDetector,)

    # work out what goes in NDPluginBase, and what does in mjpgServer.db        
    def __init__(self, WWWPORT = 8080, WWWPATH = '$(MJPGSERVER)/www', **args):
        Q = args["R"].rstrip(":")
        args["R"] = Q + ":"        
        # store the args
        self.__dict__.update(args)
        self.WWWPORT = WWWPORT
        self.WWWPATH = WWWPATH
        # make an instance of NDPluginBase
        NDPluginBase(**args)
        # initialise the Substitutions class
        self.__super.__init__(P = args["P"], Q = Q, PORT = args["PORT"])    

    # __init__ arguments
    ArgInfo = NDPluginBase.ArgInfo + makeArgInfo(__init__,
        WWWPORT = Simple('Server http port', int),
        WWWPATH = Simple('Path to www directory', str))

    # Substitution attributes
    Arguments = ('P', 'Q', 'PORT')
    TemplateFile = 'mjpgServer.db'

    # Device attributes
    LibFileList = ['mjpgServer']
    DbdFileList = ['mjpgServer']            
                        
    def Initialise(self):
        print 'mjpgServerConfigure("%(PORT)s", %(QUEUE)d, %(BLOCK)d, "%(NDARRAY_PORT)s", "%(NDARRAY_ADDR)s", %(WWWPORT)d, "%(WWWPATH)s")'%self.__dict__
