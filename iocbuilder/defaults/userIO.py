from iocbuilder import Substitution, SetSimulation
from iocbuilder.arginfo import *

class Hy8401continuous_100k(Substitution):
    '''Continuous capturing of 1 8401 channel at 100KHz'''

    def __init__(self, P, C, CH1, S = 0, NELM = 50000, FTVL = 'FLOAT', name = ''):
        self.__super.__init__(**filter_dict(locals(), self.Arguments))
    
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P    = Simple('Device Prefix', str),
        C    = Simple('Card Number', int),
        CH1  = Simple('Suffix for channel 1', str),
        S    = Simple('Signal Number', int),
        NELM = Simple('Number of elements', int),
        FTVL = Simple('Value format', str),
        name = Simple('Object name', str))

    
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'Hy8401continuous_100k.template'

# inform iocbuilder that there is no simulation
SetSimulation(Hy8401continuous_100k, None)


# TODO: Do this with a proper ai record
class ai(Substitution):
    Simulation = False
    def __init__(self, P, R, INP, name = '', desc = '', 
            DTYP = 'Hy8401ip', SCAN = '1 second', PREC = 4, EGUL = -10, 
            EGUF = 10, EGU = 'V', LINR = 'LINEAR', gda = False):
        if gda:
            gda_name, gda_desc = (name, desc)
        else:
            gda_name, gda_desc = ('', '')
        if self.Simulation:
            INP = ''
            DTYP = 'Soft Channel'
        self.__super.__init__(**filter_dict(locals(), self.Arguments))


    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P        = Simple('Device Prefix', str),
        R        = Simple('Device Suffix', str),
        DTYP     = Simple('Device Type', str),
        INP      = Simple('Input link', str),
        SCAN     = Simple('Scan Rate', str),
        PREC     = Simple('Precision', int),
        EGUL     = Simple('EGU low scale', int),
        EGUF     = Simple('EGU full scale', int),
        EGU      = Simple('EGU', str),
        LINR     = Simple('LINR', str),
        name     = Simple('Object name, also used for gda_name if gda', str),
        desc     = Simple('Description, also used for gda_desc if gda', str),
        gda      = Simple('Set to True to export to gda', bool))

    # Substitution attributes
    TemplateFile = 'ai.template'
    Arguments = ArgInfo.Names(without = ['gda']) + ['gda_name', 'gda_desc']

# Set ai.Simulation = True if in simulation mode  
class ai_sim(ai):
    Simulation = True            
SetSimulation(ai, ai_sim)
