from iocbuilder import Substitution
from iocbuilder.arginfo import *

class Hy8401continuous_100k(Substitution):
    '''Continuous capturing of 1 8401 channel at 100KHz'''

    def __init__(self, P, C, CH1, S = 0, NELM = 50000, FTVL = 'FLOAT'):
        self.__super.__init__(**filter_dict(locals(), self.Argument))
    
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P    = Simple('Device Prefix', str),
        C    = Simple('Card Number', int),
        CH1  = Simple('Suffix for channel 1', str),
        S    = Simple('Signal Number', int),
        NELM = Simple('Number of elements', int),
        FTVL = Simple('Value format', str))
    
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'Hy8401continuous_100k.template'
    
#    StatusPv = '%(P)s:ACQUIRE'    
#    SevrPv = '%(P)s:READOUTPTR'
#    EdmEmbedded = ('Hy8401continuous_100k_embed.edl','P=%(P)s,CH1=%(CH1)s')

'''
# Do this with a proper ai record
class ai(Substitution):
    def __init__(self, P, R, DTYP, INP, SCAN, PREC, EGUL, EGUF, EGU, LINR, gda_name, gda_desc):


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
        gda_name = Simple('gda_name', str),
        gda_desc = Simple('gda_desc', str))

    # Substitution attributes
    TemplateFile = 'ai.template'
    Arguments = ['P', 'R', ('DTYP', 'Hy8401ip'), 'INP', ('SCAN', '1 second'), 
        ('PREC', 4), ('EGUL', -10), ('EGUF', 10), ('EGU', 'V'), 
        ('LINR', 'LINEAR'), ('gda_name', ''), ('gda_desc', '')
    ]
    # EdmScreen attributes
    SevrPv = '%(P)s%(R)s'
    EdmEmbedded = ('ai_embed.edl','P=%(P)s,R=%(R)s')
    # __init__ arguments    
    ArgInfo = makeArgInfo(Arguments,
        P = (str, 'Device Prefix')
        R = (str, 'Device Suffix')
        DTYP = (str, 'Device Type')
        INP = (str, 'Input link')
        SCAN = (str, 'Scan Rate')
        PREC = (int, 'Precision')
        EGUL = (int, 'EGU low scale')
        EGUF = (int, 'EGU full scale')
        EGU = (str, 'EGU')
        LINR = (str, 'LINR')
        gda_name = (str, 'gda_name')
        gda_desc = (str, 'gda_desc')
'''
