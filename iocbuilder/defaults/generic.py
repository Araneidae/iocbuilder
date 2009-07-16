from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.sscan import Sscan
from iocbuilder.modules.calc import Calc
from iocbuilder.modules.std import Std

class generic_scan(Substitution):
    ''''''
    Dependencies = (Calc,Sscan,Std)
#    IdenticalSim = True    
    
    def __init__(self, P, S = '', MPTS = 1000, Dets = [''], Posns = [''],
            Trigs = ['']):        
        args = dict(P=P, S=S, MPTS=MPTS)
        for name in ['Dets', 'Posns', 'Trigs']:
            # this is the list of strings
            l = locals()[name]
            # extend it so it's at least 8 elements long
            l += ['']*8
            # make a dict, e.g. d["D01"] = Dets[0]
            d = dict(zip(getattr(self, "_"+name), l))
            # update args with it
            args.update(d)
        self.__super.__init__(**args)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P     = Simple('Device Prefix', str),
        S     = Simple('Device Suffix', str),
        MPTS  = Simple('Maximum number of points', int),
        Dets  = List  ('Default Detector PV', 8, Simple, str),
        Posns = List  ('Default Positioner PV', 4, Simple, str),
        Trigs = List  ('Default Trigger PV', 4, Simple, str))

    # Substitution attributes
    _Dets = [ "D%02d" % i for i in range(1, 8) ]
    _Posns = [ "P%d" % i for i in range(1, 4) ]
    _Trigs = [ "T%d" % i for i in range(1, 4) ]
    Arguments = ['P', 'S', 'MPTS'] + _Dets + _Posns + _Trigs
    TemplateFile = 'generic-scan.template'
    
