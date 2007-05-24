EPICS_BASE_LIBS = '/home/epics/R3.14.8.2/base/lib/linux-x86'

import os
from ctypes import *

__all__ = []

_FunctionList = (
    ('dbFreeBase',          None, (c_void_p,)),
    ('dbReadDatabase',      c_int, (c_void_p, c_char_p, c_char_p, c_char_p)),
    ('dbAllocEntry',        c_void_p, (c_void_p,)),
    ('dbFirstRecordType',   c_int, (c_void_p,)),
    ('dbGetRecordTypeName', c_char_p, (c_void_p,)),
    ('dbNextRecordType',    c_int, (c_void_p,)),
    ('dbFreeEntry',         None, (c_void_p,)),
    ('dbCopyEntry',         c_void_p, (c_void_p,)),
    ('dbFirstField',        c_int, (c_void_p,)),
    ('dbGetFieldName',      c_char_p, (c_void_p,)),
    ('dbNextField',         c_int, (c_void_p,)),
    ('dbVerify',            c_char_p, (c_void_p, c_char_p)),
)



def _DeclareFunction(name, restype, argtypes):
    function = getattr(_mydbstatic, name)
    function.restype = restype
    function.argtypes = argtypes
    globals()[name] = function
    __all__.append(name)


_mydbstatic = CDLL(os.path.join(EPICS_BASE_LIBS, 'libdbStaticHost.so'))

for functions in _FunctionList:
    _DeclareFunction(*functions)
