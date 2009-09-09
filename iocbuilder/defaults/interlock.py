from iocbuilder import Substitution, SetSimulation
from iocbuilder.arginfo import *

from iocbuilder.modules.vacuumValve import vacuumValveRead
from iocbuilder.modules.HostLink import HostLink

class interlock(Substitution):
    Dependencies = (HostLink,)

    # get the device and port from the vacuumValveReadTemplate object, then
    # init 
    def __init__(self, crate, interlock, desc, addr, name = '', ilks = ['']):
        self.__super.__init__(
            device = crate.args['device'],
            port = crate.args['port'],
            interlock = interlock,
            name = name,
            desc = desc,
            addr = "%02d" % addr,
            **dict(zip(self._ilks, ilks + [''] * 16)))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        crate     = Ident ('vacuumValveReadTemplate object', vacuumValveRead),
        interlock = Simple('interlock suffix (e.g. :INT1)', str),
        desc      = Simple('Permit description (e.g. Front end permit)', str),
        addr      = Simple('Address (1 to 10) in PLC', int),
        name      = Simple('Object name', str),
        ilks      = List  ('Interlock description (e.g. Water OK)',
            16, Simple, str))

    # Substitution attributes  
    _ilks = ['ilk%X' % i for i in range(16)]
    Arguments = ['device','port'] + \
        ArgInfo.Names(without = ['crate', 'ilks']) + _ilks
    TemplateFile = 'interlock.template'

# inform iocbuilder this has no simulation
SetSimulation(interlock, None)
