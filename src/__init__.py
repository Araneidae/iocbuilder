'''Epics IOC application building framework.

This library provides a framework for automatically generating EPICS
databases, startup scripts and even complete applications.

The following code illustrates a simple use of the library to generate 
eight records, named AI0 to AI7, one for each of the channels of an 8401
in IP socket A of a carrier card in VME slot 4:

    from epics import *

    card = hardware.Hy8002(4)
    adc = card.Hy8401(0, intEnable=1)

    for chan in range(8):
        ch = adc.channel(chan)
        ch.ai('AI%d' % chan, SCAN = 'I/O Intr', LINR = 'LINEAR',
              EGUL = -10, EGUF = 10, EGU = 'V', PREC = 3)
              
    WriteRecords('test.db')
    WriteHardware('st.cmd')

This approach is suitable for simple test applications, but for a more
general approach (for example, the generation of complete buildable iocs)
it is necessary to configure the epics module.  For example:

    import epics
    epics.Configure(... whatever ...)
    from epics import *
    ... carry on in the new environment ...

Note that changing the epics configuration will change the set of names
exported by the epics module: hence the line "from epics import *" after
the call to Configure.  For example, to configure the use of Diamond
convention names under Epics 3.13 the following configuration call is
suitable:

    import epics
    epics.Configure(recordnames=epics.DiamondRecordNames())
    from epics import *

There is much more to describe.  Watch this space...
'''

from support import ExportModules, ExportAllModules

import hardware
from hardware import _epics

__all__ = ['hardware']
__all__ += ExportModules(globals(),
    'support', 'dbd',
    'libversion', 'recordbase', 'recordset', 'iocinit', 'device',
    'fanout', 'recordnames', 'iocwriter',
    'configure')    # Best to load configure module last

for name in __all__:
    _epics._add_symbol(name, globals()[name])
_epics._add_symbol('ExportAllModules', ExportAllModules)
    
hardware._import()


# Hacks for configure support.  The Configure class is allowed to edit the
# set of symbols exported by the epics module: it does so through these two
# methods below.
def _add_symbol(name, value):
    __all__.append(name)
    globals()[name] = value
    _epics._add_symbol(name, value)

def _delete_symbol(name):
    del __all__[__all__.index(name)]
    del globals()[name]
    _epics._delete_symbol(name)

def _globals():
    return globals()

Configure._Configure__add_symbol = staticmethod(_add_symbol)
Configure._Configure__delete_symbol = staticmethod(_delete_symbol)
Configure._Configure__globals = staticmethod(_globals)

del ExportModules, ExportAllModules
del _add_symbol, _delete_symbol, _globals


# Finally set up the default configuration: basic record names, simple
# application generation, and load the default 3.13 versions file.
Configure(
    recordnames = BasicRecordNames(),
    iocwriter = SimpleIocWriter())
Configure.LoadVersionFile('versions_3_13.py')
