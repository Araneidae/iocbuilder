import os
from ctypes import *

import paths


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
    ('dbGetPrompt',         c_char_p, (c_void_p,)),
    ('dbGetPromptGroup',    c_int, (c_void_p,)),
    ('dbGetFieldType',      c_int, (c_void_p,)),
    ('dbGetNMenuChoices',   c_int, (c_void_p,)),
    ('dbGetMenuChoices',    c_void_p, (c_void_p,)),
    ('dbNextField',         c_int, (c_void_p,)),
    ('dbGetString',         c_char_p, (c_void_p,)),
    ('dbVerify',            c_char_p, (c_void_p, c_char_p)),
)



# This function is called late to complete the process of importing all the
# exports from this module.  This is done late so that paths.EPICS_BASE can be
# configured late.
def ImportFunctions():
    libdb = CDLL(os.path.join(
        paths.EPICS_BASE, 'lib', paths.EPICS_HOST_ARCH, 'libdbStaticHost.so'))

    for name, restype, argtypes in _FunctionList:
        function = getattr(libdb, name)
        function.restype = restype
        function.argtypes = argtypes
        globals()[name] = function
