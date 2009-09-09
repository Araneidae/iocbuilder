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
    
    def __init__(self, P, R, PORT, TIMEOUT = 1, ADDR = 0, **args):
        # These arguments are used by associated, rely on them to pick them up
        # before passing them down to ADBase
        locals().update(args)
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P       = Simple('Device Prefix', str),
        R       = Simple('Device Suffix', str),
        PORT    = Simple('Asyn Port name', str),
        TIMEOUT = Simple('Timeout', int),
        ADDR    = Simple('Asyn Port address', int))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'ADBase.template'

class NDPluginBase(ADBase):

    def __init__(self, NDARRAY_PORT, NDARRAY_ADDR = 0, **args):
        # These arguments are used by associated, rely on them to pick them up
        # before passing them down to ADBase
        locals().update(args)
        self.__super.__init__(**filter_dict(locals(), self.Arguments))
        
    # __init__ arguments
    ArgInfo = ADBase.ArgInfo + makeArgInfo(__init__,        
        NDARRAY_PORT = Simple('Input Array Port', str),
        NDARRAY_ADDR = Simple('Input Array Address', str))

    # Same but with a few more records
    Arguments = ArgInfo.Names()    
    TemplateFile = 'NDPluginBase.template'
                        
class NDROIN(Substitution):
    # Substitution attributes
    Arguments = ADBase.Arguments +  ['HIST_SIZE']
    TemplateFile = 'NDROIN.template'

class NDROI(Substitution, Device):
    Dependencies = (AreaDetector,)
    
    def __init__(self,
            MEMORY, NROI = 1, HIST_SIZE = 256, QUEUE = 16,
            BLOCK = 0, BUFFERS = 16,  **args):
        # store things
        ADDR = 0        
        locals().update(args)
        self.__dict__.update(locals())
        # make NROI instances of NROIN
        for i in range(NROI):            
            dargs = filter_dict(locals(), NDROIN.Arguments)
            dargs['R'] += "%s:"%i
            dargs['ADDR'] = i
            NDROIN(**dargs)
        # make an instance of NDPluginBase
        pb = NDPluginBase(**filter_dict(locals(),NDPluginBase.ArgInfo.Names()))
        self.__dict__.update(pb.args)        
        # init the substitution
        self.__super.__init__(**filter_dict(locals(),self.Arguments))

    # __init__ arguments
    ArgInfo = NDPluginBase.ArgInfo + makeArgInfo(__init__,
        MEMORY    = Simple(
            'Max memory to allocate, should be maxw*maxh*nbuffer for driver'
            ' and all attached plugins', int),    
        NROI      = Simple('Number of ROIs', int),
        HIST_SIZE = Simple('Histogram size', int),
        QUEUE     = Simple('Queue size', int),
        BLOCK     = Simple('Blocking callbacks', int),
        BUFFERS   = Simple(
            'Maximum number of NDArray buffers to be created for plugin'
            ' callbacks', int))

    # Substitution attributes
    Arguments = ADBase.Arguments
    TemplateFile = 'NDROI.template'
                
    def Initialise(self):
        print 'drvNDROIConfigure("%(PORT)s", %(QUEUE)d, %(BLOCK)d,' \
            ' "%(NDARRAY_PORT)s", "%(NDARRAY_ADDR)s", %(NROI)d,' \
            ' %(BUFFERS)d, %(MEMORY)d)' % self.__dict__

class simDetector(Device):
    '''Creates a simulation detector'''
    
    # work out with args are for firewireDCAM.db, and which are for ADBase
    def __init__(self, WIDTH, HEIGHT, MEMORY, BUFFERS = 16, **args):        
        locals().update(args)
        self.__dict__.update(locals())        
        ADBase(**filter_dict(locals(), ADBase.ArgInfo.Names()))
        self.__super.__init__()

    # __init__ arguments
    ArgInfo = ADBase.ArgInfo + makeArgInfo(__init__,
        WIDTH  = Simple('Image Width', int),
        HEIGHT = Simple('Image Height', int),
        MEMORY  = Simple(
            'Max memory to allocate, should be maxw*maxh*nbuffer for driver'
            ' and all attached plugins', int),        
        BUFFERS = Simple('Maximum number of NDArray buffers to be created for'
            ' plugin callbacks', int))
        
    # Device attributes
    LibFileList = ['simDetector']
    DbdFileList = ['simDetectorSupport']    

    def Initialise(self):
        # ADBase has stored these for us       
        print 'simDetectorConfig("%(PORT)s", %(WIDTH)s, %(HEIGHT)s, 1,' \
            ' %(BUFFERS)d, %(MEMORY)d)' % self.__dict__
