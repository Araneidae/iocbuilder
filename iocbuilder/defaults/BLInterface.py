from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.sscan import Sscan
from iocbuilder.modules.calc import Calc
from iocbuilder.modules.std import Std
from iocbuilder.modules.asyn import Asyn

class _BLInterfaceDeps(Substitution):
    Dependencies = (Sscan, Calc, Std, Asyn)
    IdenticalSim = True

class BLControl_callback(_BLInterfaceDeps):
    """Control of FE valves, shutters to be loaded on beamline side"""
    
    # Make sure the absorber is a 2 digit int
    def __init__(self, BEAMLINE, ABSB):
        ABSB = "%02d" % ABSB
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        BEAMLINE = Simple('Beamline number, (e.g. 11I)', str),
        ABSB     = Simple('Absorber number (normally 1 or 2)', int))

    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'BLControl_callback.template'
    
class BLInterface(BLControl_callback):
    """Control of FE valves, shutters to be loaded on FE side"""

    # Substitution attributes
    TemplateFile = 'BLInterface.template'

class BLFE(_BLInterfaceDeps):
    """Control of an FE motor, to be loaded on beamline side"""    
    
    # __init__ arguments
    ArgInfo = makeArgInfo(
        P = Simple('Device Prefix', str),
        M = Simple('Device Suffix', str))

    # Substitution attributes
    Arguments = ['P', 'M']
    TemplateFile = 'BLFE.template'

class FEBL(BLFE):
    """Control of an FE motor, to be loaded on FE side"""
    
    # Substitution attributes
    TemplateFile = 'FEBL.template'
    
