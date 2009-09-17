from iocbuilder import ModuleBase, Substitution, SetSimulation, IocDataStream
from iocbuilder.arginfo import *

from iocbuilder.modules.tpmac import tpmac, CS, DeltaTau, PmcSubstitution
from iocbuilder.modules.motor import basic_asyn_motor
from iocbuilder.modules.calc import Calc

import os, sys

sys.path.append(
    '/dls_sw/work/common/python/test/packages/dls_motorhome-0.0-py2.4.egg')
from dls_motorhome import PLC as _PLC


_PLCArgs = dict(
    htype = Enum('Homing types:\n' 
        'HOME = 0    # Dumb home\n' 
        'LIMIT = 1   # Home on a limit switch\n' 
        'HSW = 2     # Home on a home switch\n' 
        'HSW_HLIM = 3 # Home on a home switch close to HLIM\n' 
        'HSW_DIR = 4 # Home on directional limit switch (Newport style)\n' 
        'RLIM = 5    # Home on release of a limit\n', 
        ['HOME', 'LIMIT', 'HSW', 'HSW_HLIM', 'HSW_DIR', 'RLIM']),
    jdist = Simple(
        'Distance to jog by after finding the trigger. Should always be '
        'in a -hdir. E.g if ix23 = -1, jdist should be +ve. This should only '
        'be needed for reference marks or bouncy limit switches. A '
        'recommended value in these cases is about 1000 counts '
        'in -hdir.', int),
    post = Simple(
        'Where to move after the home. This can be:\n'
        '* None: Stay at the home position\n'
        '* an integer: move to this position in motor cts\n'
        '* "i": go to the initial position '
            '(does nothing for HOME htype motors)\n'
        '* "l": go to the low limit (ix13)\n'
        '* "h": go to the high limit (ix14)\n', str)
)


class _autohome_PMC(PmcSubstitution):
    Arguments = ()
    TemplateDir = None


class autohome(Substitution):
    Dependencies = (tpmac,)
    # Substitution attributes
    _Grps = ['GRP%d'%i for i in range(1, 8)]
    _States = ['STATE%d'%i for i in range(11, 15)]
    Arguments = ['PORT', 'P', 'PLC', 'name'] + _Grps + _States
    TemplateFile = 'autohome.template'
   
    def __init__(self, Controller, P, PLC, name = '', Groups = ['All'], 
            States = [], timeout=600000, htype=0, jdist=0, post=None):
        self.__dict__.update(locals())
        # now make the template
        self.plc = _PLC(PLC, ctype = Controller.ctype, timeout = timeout, 
            htype = htype, jdist = jdist, post = post)
        self.fname = 'PLC%02d_%s_homing.plc' % (PLC, P)
        _autohome_PMC(Controller, self.fname)

        args = dict(zip(self._Grps, (Groups + ['']*7)[:7]))
        args.update(dict(zip(self._States, (States + ['']*4)[:4])))      
        self.__super.__init__(
            PORT = Controller.PortName, P=P, PLC=PLC, name=name, **args)

    def AddMotor(self, axis, **args):
        self.plc.add_motor(axis, **args)

    def Finalise(self):
        IocDataStream(self.fname).write(self.plc.returnText())

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = Ident ('PMAC or GeoBrick', DeltaTau),
        P          = Simple('Device Prefix', str),
        PLC        = Simple('PLC Number', int),
        Groups     = List  (
            'Text strings for Group 1..7 labels', 7, Simple, str),
        States     = List  (
            'Text strings for State 11..14 labels', 4, Simple, str),
        name       = Simple('Object name', str),   
        timeout    = Simple('Move timeout', int),        
        **_PLCArgs)        
                        
SetSimulation(autohome, None)

class dls_pmac_asyn_motor(basic_asyn_motor):
    Dependencies = (tpmac, Calc)

    def __init__(self, HOME=None, 
            group=1, htype = None, jdist = None, post = None, **args):
        if HOME is None:
            HOME = args['P']
        else:
            HOME.AddMotor(int(args['ADDR']), group = group, 
                htype = htype, jdist = jdist, post = post)
            HOME = HOME.P                    
        self.__super.__init__(
            HOME = HOME, SPORT = args['Controller'].PortName, **args)

    ArgInfo = basic_asyn_motor.ArgInfo + makeArgInfo(__init__,
        HOME  = Ident ('Autohome template instance', autohome),
        group = Choice('Group number for autohoming', range(8)),
        **_PLCArgs)

    # Substitution attributes
    Arguments = basic_asyn_motor.Arguments + ['SPORT', 'HOME']
    TemplateFile = 'dls_pmac_asyn_motor.template'

def dls_pmac_asyn_motor_sim(HOME=None, group=1, timeout = None, htype = None, 
        jdist = None, post = None, **args):
    # if it's a simulation, just connect it to a basic_asyn_motor 
    return basic_asyn_motor(**args)
SetSimulation(dls_pmac_asyn_motor, dls_pmac_asyn_motor_sim)



class PMCFile(PmcSubstitution):
    Arguments = ()
    ArgInfo = makeArgInfo(
        Controller = Ident ('PMAC or GeoBrick', DeltaTau),
        Filename   = Simple('PMC Filename', str))

class CS_blade_slits(PmcSubstitution): 
    def __init__(self, CS, BP='', BM='', PLC=None):
        assert CS.CS in range(2, 10), 'Can only use CS 2..9'
        if PLC is None:
            PLC = CS.CS + 15    
        self.__super.__init__(Controller=CS, 
            COORD = CS.CS, **filter_dict(locals(), self.ArgInfo.Names()))

    TemplateFile = 'CS_blade_slits.pmc'
    Arguments = ['COORD', 'CS', 'BP', 'BM', 'PLC']
        
    ArgInfo = makeArgInfo(__init__,
        CS  = Ident ('CS object', CS),
        BP  = Simple('Blade Plus Axis Number', str),
        BM  = Simple('Blade Minus Axis Number', str),
        PLC = Simple('PLC number, defaults to CS number+15', int))


class _CS_3jack_PMC(PmcSubstitution):
    TemplateFile = 'CS_3jack.pmc'
    Arguments = [
        'COORD', 'MD', 'J1', 'J3', 'J1Z', 'J2', 'J1X', 'MCX', 'PLC', 'J2X',
        'J3X', 'J2Z', 'J3Z', 'MCZ']

class CS_3jack(Substitution):
    def __init__(self,
            CS, P, J1, J1X, J1Z, J2, J2X, J2Z, J3, J3X, J3Z,
            MD, MCX, MCZ, PLC = None, name = '', **kwargs):
        locals().update(kwargs)
        COORD = CS.CS        
        assert COORD in range(2, 10), 'Can only use CS 2..9'    
        if PLC is None:
            PLC = COORD + 15
        PORT=CS.PortName            
        self.PmcClass(CS, **filter_dict(locals(), self.PmcClass.Arguments))
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        CS   = Ident ('CS object', CS),
        P    = Simple('Device Prefix', str),
        J1   = Simple('Axisnum for jack 1', int),
        J1X  = Simple('Global X co-ord of J1 base in EGU, e.g. 0', float),
        J1Z  = Simple('Global Z co-ord of J1 base in EGU, e.g. -100', float),
        J2   = Simple('Axisnum for jack 2, e.g. 3', int),
        J2X  = Simple('Global X co-ord of J2 base in EGU, e.g. 50', float),
        J2Z  = Simple('Global Z co-ord of J2 base in EGU, e.g. 100', float),
        J3   = Simple('Axisnum for jack 3, e.g. 4', int),
        J3X  = Simple('Global X co-ord of J3 base in EGU, e.g. -50', float),
        J3Z  = Simple('Global Z co-ord of J3 base in EGU, e.g. 100', float),
        MD   = Simple('Depth of actual mirror in EGU, e.g. 10', float),
        MCX  = Simple(
            'Global X co-ord of measure point in EGU, e.g. 0', float),
        MCZ  = Simple('Global Z co-ord of measure in EGU, e.g. 10', float),
        PLC  = Simple('PLC number, defaults to CS number+15', int),
        name = Simple('Object name', str))        

    Dependencies = (tpmac,)
    Arguments = ['P', 'PORT', 'COORD', 'name']
    TemplateFile = '3jack.template'
    
    PmcClass = _CS_3jack_PMC

                
class _CS_3jack_mirror_PMC(PmcSubstitution):
    TemplateFile = 'CS_3jack_mirror.pmc'
    Arguments = _CS_3jack_PMC.Arguments + ['JTX', 'JTZ', 'MP', 'MR']

class CS_3jack_mirror(CS_3jack):
    def __init__(self, JTX, JTZ, MP, MR, ROTX = 0, ROTY = 0, **kwargs):
        locals().update(kwargs)
        args = locals().copy()
        del args['self']
        self.__super.__init__(**args)

    # __init__ arguments
    ArgInfo = CS_3jack.ArgInfo + makeArgInfo(__init__,
        JTX  = Simple('Jack plane X co-ord of J1 top in EGU, e.g. 20', float),
        JTZ  = Simple('Jack plane Z co-ord of J1 top in EGU, e.g. 20', float),
        MP   = Simple('Pitch of mirror support in deg, e.g. 45', float),
        MR   = Simple('Roll of mirror support in deg, e.g. 45', float),
        ROTX = Simple('Rotate 3D view around X axis by 90deg*ROTX', int),
        ROTY = Simple('Rotate 3D view around Y axis by 90deg*ROTY', int),
    )
    
    Arguments = CS_3jack.Arguments + ['ROTX', 'ROTY']
    TemplateFile = '3jack-mirror.template'
    
    PmcClass = _CS_3jack_mirror_PMC


SetSimulation(CS_3jack, None)     
SetSimulation(CS_3jack_mirror, None)

'''        
class PLC2_motion_stop(_pmcInclude):
    def __init__(self, Controller, STOPTIME = 500):
        self.__super.__init__(
            Controller=Controller, Filename='PLC2_motion_stop.pmc',
            STOPTIME=STOPTIME)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = (str, 'PMAC or GeoBrick'),
        STOPTIME = (int,
            'Time between stopping motors and killing motors in ms'),
    )

class PLC3_micromech_enable(_pmcInclude):
    def __init__(self, Controller):
        self.__super.__init__(
            Controller=Controller, Filename='PLC3_micromech_enable.pmc',
            STOPTIME=STOPTIME)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = (str, 'PMAC or GeoBrick'),
    )
'''

class PLC4_encoder_loss(PmcSubstitution):
    def __init__(self, Controller, On):
        On = (On + [False]*32)[:32]
        adict = dict(
            ('ONM%d' % (i + 1), int(bool(o))) for i, o in enumerate(On))
        self.__super.__init__(Controller=Controller, **adict)
        
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = Ident ('PMAC or GeoBrick', DeltaTau),
        On         = List  ('Axis encoder loss toggle', 32, Simple, bool))

    TemplateFile = 'PLC4_encoder_loss.pmc'
    Arguments = ['ONM%d' % (i + 1) for i in range(32)]
 

class PROG10_CS_motion(PmcSubstitution):
    # __init__ arguments
    ArgInfo = makeArgInfo(
        Controller = Ident('PMAC or GeoBrick', DeltaTau))

    TemplateFile = 'PROG10_CS_motion.pmc'
    Arguments = ()
