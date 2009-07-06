from iocbuilder import Substitution
from iocbuilder.arginfo import *

class gateway_control(Substitution):    

    # __init__ arguments
    ArgInfo = makeArgInfo(
        GATEWAY = Simple('Gateway name', str))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'gateway_control.template'
