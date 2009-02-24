from iocbuilder import Substitution
from iocbuilder.validators import TwoDigitInt


class BLControl_callback(Substitution):
    # __init__ arguments
    ArgInfo = [
        ('BEAMLINE', str, 'Beamline number, (e.g. 11I)'),
        ('ABSB', TwoDigitInt, 'Absorber number (normally 1 or 2)')        
    ]
    # Substitution attributes
    TemplateFile = 'BLControl_callback.template'
    
