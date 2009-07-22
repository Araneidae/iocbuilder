from iocbuilder import ModuleBase, Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.tpmac import tpmac, CS
from iocbuilder.modules.motor import basic_asyn_motor
from iocbuilder.modules.calc import Calc

import os, sys

#sys.path.append("/dls_sw/work/common/python/test/packages/dls_motorhome-0.0-py2.4.egg")      
#from dls_motorhome import PLC

'''
HOMING_TYPES = ["""Homing types:
HOME = 0      # Dumb home
LIMIT = 1     # Home on a limit switch
HSW = 2       # Home on a home switch
HSW_HLIM = 3  # Home on a home switch close to HLIM
HSW_DIR = 4   # Home on a directional limit switch (Newport style)
RLIM = 5      # Home on release of a limit
"""

_PLCArgs = dict(
    timeout = (int, "Move timeout"),
    htype = (Enum(["HOME","LIMIT","HSW","HSW_HLIM","HSW_DIR","RLIM"], 
        "Homing types:\n" \
        "HOME = 0    # Dumb home\n" \
        "LIMIT = 1   # Home on a limit switch\n" \
        "HSW = 2     # Home on a home switch\n" \
        "HSW_HLIM = 3 # Home on a home switch close to HLIM\n" \
        "HSW_DIR = 4 # Home on directional limit switch (Newport style)\n" \
        "RLIM = 5    # Home on release of a limit\n"),
    jdist = (int, "Distance to jog by after finding the trigger. Should always be "\
        "in a -hdir. E.g if ix23 = -1, jdist should be +ve. This should only be "\
        "needed for reference marks or bouncy limit switches. A recommended "\
        "value in these cases is about 1000 counts in -hdir."),
    post = (str, 'Where to move after the home. This can be:\n'\
        '* None: Stay at the home position\n'\
        '* an integer: move to this position in motor cts\n'\
        '* "i": go to the initial position (does nothing for HOME htype motors)\n'\
        '* "l": go to the low limit (ix13)\n'\
        '* "h": go to the high limit (ix14)\n')
)  

class autohome(EdmScreen,Substitution):
    Dependencies = (tpmac,)
    # Substitution attributes
    _Grps = [ "GRP%d"%i for i in range(1,8) ]
    _States = [ "STATE%d"%i for i in range(11,15) ]
    Arguments = ["PORT", "P", "PLC", "name"] + _Grps + _States
    TemplateFile = 'autohome.template'
    
    def __init__(self, Controller, P, PLC, name = '', Groups = ["All"], States = [], htype=None, 
        jdist=None, post=None):
        self.__dict__.update(locals())
        # now make the template
        self.plc = PLC(PLC, ctype = Controller.ctype, timeout = timeout, 
            htype = htype, jdist = jdist, post = post)
        # this is a hack, tell the pmc datastream to call returnText at the last minute
        Controller.getPmc().write(self.plc.returnText)        
        args = dict(zip(self._Grps, (Groups + [""]*7)[:7]))
        args.update(dict(zip(self._States, (States + [""]*4)[:4]))        
        self.__super.__init__(PORT = Controller.PortName, P=P, PLC=PLC, **args)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = (DeltaTau, 'PMAC or GeoBrick'),
        P = (str, 'Device Prefix'),
        PLC = (int, 'PLC Number'),
        Groups = ([str16], "Text strings for Group 1..7 labels"),
        States = ([str16], "Text strings for State 11..14 labels"),
        name = Simple('Object name', str))        
        **_PLCArgs
    )        
                        
class autohome_sim(ModuleBase):
    ArgInfo = autohome.ArgInfo[:]
'''
class autohome(ModuleBase):
    pass

class dls_pmac_asyn_motor(basic_asyn_motor):
    Dependencies = (tpmac,Calc)
#    IdenticalSim = False    

    def __init__(self, HOME=None, 
#            group=1, timeout = None, htype = None, jdist = None, post = None, 
            **args):
        if HOME is None:
            HOME = args["P"]
#        else:
#            HOME.plc.add_motor( int(args["ADDR"]), group = group, 
#                timeout = timeout, htype = htype, jdist = jdist, post = post)
#            HOME = HOME.P                    
        self.__super.__init__(HOME = HOME, SPORT = args["Controller"].PortName, 
            **args)

    ArgInfo = basic_asyn_motor.ArgInfo + makeArgInfo(__init__,
        HOME = Ident ('Autohome template instance', autohome),
#        group = (Choice(*range(1,8), 'Group number for autohoming'),
#        **_PLCArgs
    )

    # Substitution attributes
    Arguments = basic_asyn_motor.Arguments + ['SPORT','HOME']
    TemplateFile = 'dls_pmac_asyn_motor.template'

'''
def dls_pmac_asyn_motor_sim(HOME=None, group=1, timeout = None, htype = None, 
        jdist = None, post = None, **args):
    # if it's a simulation, just connect it to a basic_asyn_motor 
    return basic_asyn_motor(**args)
dls_pmac_asyn_motor_sim.ArgInfo = dls_pmac_asyn_motor.ArgInfo

class _pmcInclude(ModuleBase):
    Dependencies = (tpmac,)
    def __init__(self,Controller,Filename,**args):
        filename = self.ModuleFile(os.path.join('data', Filename))
        Controller.IncludePmc(filename,args)
        self.__super.__init__()

class PMCFile(_pmcInclude):
    ArgInfo = makeArgInfo(_pmcInclude.__init__
        Controller = (DeltaTau, 'PMAC or GeoBrick'),
        Filename = (str, 'PMC Filename')
    )

class CS_blade_slits(_pmcInclude):
    ArgInfo = makeArgInfo(__init__,
        CS = (CS, 'CS object'),
        BP = (str, 'BP'),
        BM = (str, 'BM'),
        PLC = (int, 'PLC number, defaults to CS number+15')
    )        
    def __init__(self, CS, BP='', BM='', PLC=None):
        assert CS.CS in range(2,10), "Can only use CS 2..9"
        args = locals().copy()
        del args["self"]
        def args["CS"]
        args["COORD"] = CS.CS
        if args["PLC"] is None:
            args["PLC"] = args["COORD"]+15    
        self.__super.__init__(Controller=CS,Filename="CS_blade_slits.pmc",**args)  
'''

'''
class CS_3jack(Substitution, EdmScreen):
    Dependencies = (tpmac,)
    Arguments = ("P","PORT","COORD", "name")
    TemplateFile = '3jack.template' 
    PmcFile = "CS_3jack.pmc"

    def __init__(self, CS, P, J1, J1X, J1Z, J2, J2X, J2Z, J3, J3X, J3Z, MD, MCX, MCZ, PLC = None, name = '', **kwargs):
        locals().update(kwargs)
        args = locals().copy()
        del args["self"]
        del args["CS"]       
        del args["kwargs"] 
        assert CS.CS in range(2,10), "Can only use CS 2..9"    
        args["COORD"] = CS.CS
        if args["PLC"] is None:
            args["PLC"] = args["COORD"]+15
        _pmcInclude(CS,self.PmcFile,**args)
        self.__super.__init__(P=P, PORT=CS.PortName, COORD=CS.CS)        

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        CS = (CS, 'CS object'),
        P = (str, 'Device Prefix'),
        J1 = (int, 'Axisnum for jack 1'),
        J1X = (float, 'Global X co-ord of J1 base in EGU, e.g. 0'),
        J1Z = (float, 'Global Z co-ord of J1 base in EGU, e.g. -100'),
        J2 = (int, 'Axisnum for jack 2, e.g. 3'),
        J2X = (float, 'Global X co-ord of J2 base in EGU, e.g. 50'),
        J2Z = (float, 'Global Z co-ord of J2 base in EGU, e.g. 100'),
        J3 = (int, 'Axisnum for jack 3, e.g. 4'),
        J3X = (float, 'Global X co-ord of J3 base in EGU, e.g. -50'),
        J3Z = (float, 'Global Z co-ord of J3 base in EGU, e.g. 100'),
        MD = (float, 'Depth of actual mirror in EGU, e.g. 10'),
        MCX = (float, 'Global X co-ord of measure point in EGU, e.g. 0'),
        MCZ = (float, 'Global Z co-ord of measure in EGU, e.g. 10'),
        PLC = (int, 'PLC number, defaults to CS number+15'),
        name = Simple('Object name', str))        
    )
     
class CS_3jack_mirror(CS_3jack):

    Arguments = ("P","PORT","COORD","ROTX","ROTY")
    TemplateFile = '3jack-mirror.template' 
    PmcFile = "CS_3jack_mirror.pmc"

    def __init__(self, JTX, JTZ, MP, MR, ROTX = 0, ROTY = 0, **kwargs):
        locals().update(kwargs)
        self.__super.__init__(self, **locals())

    # __init__ arguments
    ArgInfo = CS_3jack.ArgInfo + makeArgInfo(__init__,
        JTX = (float, 'Jack plane X co-ord of J1 top in EGU, e.g. 20'),
        JTZ = (float, 'Jack plane Z co-ord of J1 top in EGU, e.g. 20'),
        MP = (float, 'Pitch of mirror support in deg, e.g. 45'),
        MR = (float, 'Roll of mirror support in deg, e.g. 45'),
        ROTX = (int, 'Rotate 3D view around X axis by 90deg*ROTX'),
        ROTY = (int, 'Rotate 3D view around Y axis by 90deg*ROTY'),
    )

    
class PLC2_motion_stop(_pmcInclude):
    def __init__(self, Controller, STOPTIME = 500):
        self.__super.__init__(Controller=Controller,Filename='PLC2_motion_stop.pmc',STOPTIME=STOPTIME)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = (str, 'PMAC or GeoBrick'),
        STOPTIME = (int, 'Time between stopping motors and killing motors in ms'),
    )

class PLC3_micromech_enable(_pmcInclude):
    def __init__(self, Controller):
        self.__super.__init__(Controller=Controller,Filename='PLC3_micromech_enable.pmc',STOPTIME=STOPTIME)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = (str, 'PMAC or GeoBrick'),
    )

class PLC4_encoder_loss(_pmcInclude):
    def __init__(self, Controller, Axes):
        flags = [0] * 32
        for ax in axes:
            assert ax in range(1,33), "axis %d not a valid pmac number"
        self.__super.__init__(Controller=Controller,Filename='PLC3_micromech_enable.pmc',STOPTIME=STOPTIME)
    # __init__ arguments
    ArgInfo = [
        ('Controller', None, 'PMAC or GeoBrick'), ] + [
        ('ONM%d'%m, int, 'Activate encoder loss protection for axis %d, 0=Off, 1=On'%m, 0) for m in range(1,33)
    ]
    def __init__(self,Controller,**args):
        self.__super.__init__(Controller=Controller,Filename='PLC4_encoder_loss.pmc',**args)

class PROG10_CS_motion(_pmcInclude):
    # __init__ arguments
    ArgInfo = [
        ('Controller', None, 'PMAC or GeoBrick'),
    ]
    def __init__(self,Controller,**args):
        self.__super.__init__(Controller=Controller,Filename='PROG10_CS_motion.pmc',**args)

'''
