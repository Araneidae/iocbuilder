from iocbuilder import Substitution
from iocbuilder.arginfo import *

from iocbuilder.modules.vacuumValve import vacuumValveRead
from iocbuilder.modules.HostLink import HostLink

class interlock(Substitution):
    Dependencies = (HostLink,)

    # get the device and port from the vacuumValveReadTemplate object, then
    # init 
    def __init__(self, crate, interlock, desc, addr, ilks = ['']):
        args = dict(        
            zip(self._ilks, ilks + [''] * 16),
            device = crate.args["device"],
            port = crate.args["port"],
            interlock = interlock,
            desc = desc,
            addr = "%02d" % addr)
        self.__super.__init__(**args)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        crate     = Ident ('vacuumValveReadTemplate object', vacuumValveRead),
        interlock = Simple('interlock suffix (e.g. :INT1)', str),
        desc      = Simple('Permit description (e.g. Front end permit)', str),
        addr      = Simple('Address (1 to 10) in PLC', int),
        ilks      = List  ('Interlock description (e.g. Water OK)',
            16, Simple, str))

    # Substitution attributes  
    _ilks = [ 'ilk%X' % i for i in range(16) ]
    Arguments = ['device','port'] + \
        ArgInfo.Names(without = ['crate', 'ilks']) + _ilks
    TemplateFile = 'interlock.template'

#    EdmEmbedded = ('interlock-embed.edl', 'device=%(device)s%(interlock)s')
#    EdmScreen = ('interlocks.edl', 'device=%(device)s%(interlock)s')
