from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

from iocbuilder.modules.asyn import Asyn
from iocbuilder.modules.busy import Busy

__all__ = ['AreaDetector']

class AreaDetector(Device):
    Dependencies = (Asyn, Busy)
    LibFileList = ['ADBase', 'NDPlugin']
    DbdFileList = ['pluginSupport']    
    AutoInstantiate = True

class ADBase(Substitution):
    Dependencies = (AreaDetector,)    
    
    def __init__(self, P, R, PORT, MEMORY, BUFFERS = 16, TIMEOUT = 1):
        # These arguments are used by associated, rely on them to pick them up
        # before passing them down to ADBase
        ADDR = 0
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P       = Simple('Device Prefix', str),
        R       = Simple('Device Suffix', str),
        PORT    = Simple('Asyn Port name', str),
        MEMORY  = Simple('Max memory to allocate, should be maxw*maxh*nbuffer for driver and all attached plugins', int),
        BUFFERS = Simple('Maximum number of NDArray buffers to be created for plugin callbacks', int),
        TIMEOUT = Simple('Timeout', int))

    # Substitution attributes
    Arguments = ('P', 'R', 'PORT', 'ADDR', 'TIMEOUT')    
    TemplateFile = 'ADBase.template'

class NDPluginBase(ADBase):

    def __init__(self, NDARRAY_PORT, NDARRAY_ADDR = 0, QUEUE = 16, BLOCK = 0, **args):
        # ADBase will filter our argument for us, so just give it everything
        self.__super.__init__(NDARRAY_PORT = NDARRAY_PORT, 
            NDARRAY_ADDR = NDARRAY_ADDR, **args)

    # __init__ arguments
    ArgInfo = ADBase.ArgInfo + makeArgInfo(__init__,
        NDARRAY_PORT = Simple('Input Array Port', str),
        NDARRAY_ADDR = Simple('Input Array Address', str),
        QUEUE        = Simple('Queue size', int),
        BLOCK        = Simple('Blocking callbacks', int))

    # Substitution attributes
    Arguments = ('P', 'R', 'PORT', 'ADDR', 'TIMEOUT', 'NDARRAY_PORT', 'NDARRAY_ADDR')    
    TemplateFile = 'NDPluginBase.template'
        
class NDROIN(Substitution):
    Dependencies = (AreaDetector,)
    # __init__ arguments
    Arguments = ('P', 'R', 'PORT', 'ADDR', 'TIMEOUT', 'HIST_SIZE')
    # Substitution attributes
    TemplateFile = 'NDROIN.template'

class NDROI(Substitution, Device):
    Dependencies = (AreaDetector,)
    
    def __init__(self, NROI = 1, HIST_SIZE = 256, **args):
        # store things
        self.__dict__.update(args)
        self.NROI = NROI
        locals().update(args)
        ADDR = 0
        # make NROI instances of NROIN
        for i in range(NROI):            
            dargs = dict((k,locals()[v]) for k in NDROIN.Arguments)
            dargs['R'] += "%s:"%i
            dargs['ADDR'] = i
            NDROIN(**dargs)
        # make an instance of NDPluginBase
        NDPluginBase(**args)
        # initialise the Substitutions class
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        NROI      = Simple('Number of ROIs', int),
        HIST_SIZE = Simple('Histogram size', int))

    # Substitution attributes
    Arguments = ('P', 'R', 'PORT', 'ADDR', 'TIMEOUT')
    TemplateFile = 'NDROI.template'
        
    def Initialise(self):
        print 'drvNDROIConfigure("%(PORT)s", %(QUEUE)d, %(BLOCK)d, "%(NDARRAY_PORT)s", "%(NDARRAY_ADDR)s", %(NROI)d, %(BUFFERS)d, %(MEMORY)d)'%self.__dict__
