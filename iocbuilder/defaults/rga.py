from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.streamDevice import AutoProtocol
from iocbuilder.modules.asyn import AsynOctetInterface

class rga(AutoProtocol):

    # __init__ arguments
    ArgInfo = makeArgInfo(
        device  = Simple('Device Prefix', str),
        port    = Ident ('Asyn Serial Port', AsynOctetInterface),
        channel = Simple('RGA channel number (port number of PC comm port 1-4)', int))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'rga.template'
    
    # Autotprotocol attributes
    ProtocolFiles = ['rga.protocol']
    
#    EdmScreen = ('rga','device=%(device)s')    
    
'''
class rga_sim(rga_base):
    # __init__ arguments
    ArgInfo = makeArgInfo(rga_base.Arguments,
        device = (str, 'Device Prefix')
        port = (str, 'Dummy Asyn Serial Port')
        channel = (int, 'RGA channel number (port number of PC comm port 1-4)')
    ]
    # Substitution attributes
    TemplateFile = 'simulation_rga.template'
'''
