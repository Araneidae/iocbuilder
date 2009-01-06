'''Epics IOC application building framework.

This library provides a framework for automatically generating EPICS
databases, startup scripts and even complete applications.

The following code illustrates a simple use of the library to generate 
eight records, named AI0 to AI7, one for each of the channels of an 8401
in IP socket A of a carrier card in VME slot 4:

    from dls.builder import *

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
it is necessary to configure the dls.builder module.  For example:

    import dls.builder
    dls.builder.Configure(... whatever ...)
    from dls.builder import *
    ... carry on in the new environment ...

Note that changing the builder configuration will change the set of names
exported by the builder module: hence the line "from dls.builder import *"
after the call to Configure.  For example, to configure the use of Diamond
convention names under Epics 3.13 the following configuration call is
suitable:

    import dls.builder
    dls.builder.Configure(recordnames=dls.builder.DiamondRecordNames())
    from dls.builder import *

There is much more to describe.  Watch this space...
'''

from support import ExportModules, ExportAllModules, CreateModule

hardware = CreateModule('iocbuilder.hardware')

__all__ = ['hardware']
__all__ += ExportModules(globals(),
    'support', 'dbd',
    'libversion', 'recordbase', 'recordset', 'iocinit', 'device',
    'fanout', 'recordnames', 'iocwriter',
    'configure')    # Best to load configure module last


# Hacks for configure support.  The Configure class is allowed to edit the
# set of symbols exported by the epics module: it does so through these two
# methods below.
def _add_symbol(name, value):
    __all__.append(name)
    globals()[name] = value

def _globals():
    return globals()

Configure._Configure__add_symbol = staticmethod(_add_symbol)
Configure._Configure__globals = staticmethod(_globals)

del ExportModules, ExportAllModules
del _add_symbol, _globals


