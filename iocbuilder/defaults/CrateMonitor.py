from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.streamDevice import AutoProtocol
from iocbuilder.modules.asyn import AsynOctetInterface


class CrateMonitor(Substitution, AutoProtocol):

    # __init__ arguments
    ArgInfo = makeArgInfo(
        device = Ident ('Asyn IP Port, also used for device prefix',
            AsynOctetInterface),
        name   = Simple('Object Name', str))
    
    # Substitution arguments
    Arguments = ArgInfo.Names()
    TemplateFile = 'CrateMonitor.template'        
    
    # AutoProtocol attributes
    ProtocolFiles = ['CrateMon.proto']
