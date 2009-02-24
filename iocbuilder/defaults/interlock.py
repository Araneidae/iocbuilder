from iocbuilder import Substitution
from iocbuilder.hardware import HostLink
from iocbuilder.validators import TwoDigitInt

class interlock(Substitution):
    Dependencies = (HostLink,)
    # __init__ arguments
    ArgInfo = [
        ('crate', None, 'vacuumValveReadTemplate object'),
        ('interlock', str, 'interlock suffix (e.g. :INT1)'),
        ('desc', str, 'Permit description (e.g. Front end permit)'),
        ('addr', TwoDigitInt, 'Address (1 to 10) in PLC') ] + [ 
        ('ilk%X'%num, str, 'Interlock description (e.g. Water OK)', '') 
             for num in range(16)
    ]
    # Substitution attributes  
    Arguments = ['device','port'] + [x[0] for x in ArgInfo[1:]]
    TemplateFile = 'interlock.template'
