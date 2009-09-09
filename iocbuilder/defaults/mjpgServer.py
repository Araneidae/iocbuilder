from iocbuilder import Device, Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.areaDetector import AreaDetector, NDPluginBase

class MjpgServer(Substitution, Device):
    Dependencies = (AreaDetector,)

    # work out what goes in NDPluginBase, and what does in mjpgServer.db
    def __init__(self,
            MEMORY, QUEUE = 16, BLOCK = 0, WWWPORT = 8080,
            WWWPATH = '$(MJPGSERVER)/www', **args):
        Q = args["R"].rstrip(":")
        args["R"] = Q + ":"                 
        locals().update(args)   
        self.__dict__.update(locals())
        # make an instance of NDPluginBase
        pb = NDPluginBase(
            **filter_dict(locals(), NDPluginBase.ArgInfo.Names()))
        self.__dict__.update(pb.args)                
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = NDPluginBase.ArgInfo + makeArgInfo(__init__,
        MEMORY  = Simple(
            'Max memory to allocate, should be maxw*maxh*nbuffer for driver'
            ' and all attached plugins', int),    
        QUEUE        = Simple('Queue size', int),
        BLOCK        = Simple('Blocking callbacks', int),
        WWWPORT = Simple('Server http port', int),
        WWWPATH = Simple('Path to www directory', str))

    # Substitution attributes
    Arguments = ('P', 'Q', 'PORT')
    TemplateFile = 'mjpgServer.db'

    # Device attributes
    LibFileList = ['mjpgServer']
    DbdFileList = ['mjpgServer']            
                        
    def Initialise(self):
        print 'mjpgServerConfigure(' \
            '"%(PORT)s", %(QUEUE)d, %(BLOCK)d, "%(NDARRAY_PORT)s", ' \
            '"%(NDARRAY_ADDR)s", %(WWWPORT)d, "%(WWWPATH)s")' % self.__dict__
