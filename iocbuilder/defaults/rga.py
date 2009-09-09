from iocbuilder import Substitution, SetSimulation
from iocbuilder.arginfo import *

from iocbuilder.modules.streamDevice import AutoProtocol
from iocbuilder.modules.asyn import AsynOctetInterface

class rga(AutoProtocol):

    def __init__(self, device, port, channel, name = ''):
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        device  = Simple('Device Prefix', str),
        port    = Ident ('Asyn Serial Port', AsynOctetInterface),
        channel = Simple(
            'RGA channel number (port number of PC comm port 1-4)', int),
        name    = Simple('Object name', str))               

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'rga.template'
    
    # Autotprotocol attributes
    ProtocolFiles = ['rga.protocol'] 
    
# Simulation uses different db file
class rga_sim(rga):
    TemplateFile = 'simulation_rga.template'
SetSimulation(rga, rga_sim)
