# Module for providing uplift of epics specific symbols.
# Instead of running
#       import ..epics
# which is not supported in python 2.4 this module should be imported.


__all__ = []

def _add_symbol(name, value):
    globals()[name] = value
    __all__.append(name)
