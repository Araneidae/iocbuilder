from iocbuilder import ModuleBase
from iocbuilder.arginfo import *
from iocbuilder.modules.eurotherm2k import eurotherm2k

class eurotherm2k_maker(ModuleBase):
    '''Create N eurotherm2k instances'''

    def __init__(self, P, PORT, n = 5):
        # initialise the super class, this MUST be done
        self.__super.__init__()
        # check n is in range
        assert n in range(1,10), "Can only have up to 9 on a bus"
        # create objects
        for i in range(n):
            eurotherm2k(P = P, Q = ":E%d" % i, PORT=PORT, GAD = 0, LAD = i)

    # tell xmlbuilder what args to supply
    ArgInfo = makeArgInfo(__init__,
        P    = Simple("Device Prefix", str),
        PORT = Simple("Asyn port string", str),
        n    = Simple("Number of controllers to make", int))

