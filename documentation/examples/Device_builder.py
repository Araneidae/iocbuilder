from iocbuilder import Device
from iocbuilder.arginfo import *
from iocbuilder.modules.asyn import Asyn

class my_device(Device):
    # this uses asyn
    Dependencies = (Asyn,)

    # it also uses libmy_device.so and my_deviceSupport.dbd from its own module
    LibFileList = ['my_device']
    DbdFileList = ['my_deviceSupport']

    # simple init, just store the arguments
    def __init__(self, a, b, c="c"):
        self.__super.__init__()
        self.a = a
        self.b = b
        self.c = c

    # this will appear once in the startup script if the class is instantiated
    def InitialiseOnce(self):
        print "my_device_init()"

    # this will appear once per instantiation
    def Initialise(self):
        print "my_device_configure(%(a)s, %(b)d, %(c)s)" % self.__dict__

    # tell xmlbuilder what args to supply
    ArgInfo = makeArgInfo(__init__,
        a    = Simple("Argument a", str),
        b    = Simple("Argument b", int),
        c    = Simple("Argument c", str))
