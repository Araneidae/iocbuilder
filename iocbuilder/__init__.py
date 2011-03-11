'''Epics IOC application building framework.

This library provides a framework for automatically generating EPICS
databases, startup scripts and even complete applications.

The following code illustrates a simple use of the library to generate
eight records, named AI0 to AI7, one for each of the channels of an 8401
in IP socket A of a carrier card in VME slot 4:

    from iocbuilder import *
    ConfigureIOC()

    card = hardware.Hy8002(4)
    adc = card.Hy8401(0, intEnable=1)

    for chan in range(8):
        ch = adc.channel(chan)
        ch.ai('AI%d' % chan, SCAN = 'I/O Intr', LINR = 'LINEAR',
              EGUL = -10, EGUF = 10, EGU = 'V', PREC = 3)

    WriteIoc('iocs', 'TS', 'TEST', 1)

'''

import support

## Hardware module containing all exported resources.
#
# All names exported from EPICS support modules using the \c __all__
# identifier are added to this module.
hardware = support.CreateModule('iocbuilder.hardware')

__all__ = ['hardware']
__all__ += support.ExportModules(globals(),
    'configure', 'support', 'dbd',
    'libversion', 'recordbase', 'recordset', 'iocinit', 'device',
    'fanout', 'recordnames', 'iocwriter', 'arginfo', 'autosubst', 'includeXml')


# Hacks for configure support.  The Configure class is allowed to add to the
# set of symbols exported by the epics module: it does so through this method
def _add_symbol(name, value):
    __all__.append(name)
    globals()[name] = value

Configure._Configure__add_symbol = staticmethod(_add_symbol)
del _add_symbol


