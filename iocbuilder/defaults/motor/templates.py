from iocbuilder import Substitution, Device
from iocbuilder.arginfo import *

__all__ = ['basic_asyn_motor', 'MotorController']

'''
class MotorSimLib(Device):
    Dependencies = (Asyn, Seq)
    LibFileList = [ "motorSimSupport" ]
    DbdFileList = [ "motorSimSupport" ]
    AutoInstantiate = True    
'''

class MotorController(Device):
    pass

class basic_asyn_motor(Substitution):    
    '''Basic motor record'''

    # Just grab the port name from the controller and init
    def __init__(self, Controller, ADDR, P, M, DESC, MRES, 
            gda_name = '', gda_desc = '', DTYP = 'asynMotor', 
            DIR = 0, VBAS = 0, VELO = 1.0, VMAX = None, ACCL =  0.5, 
            BDST = '', BVEL = '', BACC = '', PREC = 3, EGU = 'mm', 
            DHLM = 10000, DLLM = -10000, HLSV = 'MAJOR', INIT = '', 
            SREV = 1000, RRES = '', TWV = 0.1, ERES = '', JAR = 1000, 
            UEIP = False, OFF = 0.0, RDBD = '', FOFF = 0, **args):
        locals().update(args)
        # Default VMAX to VELO
        if VMAX is not None:
            VMAX = VELO
        # Convert UEIP to an int
        UEIP = int(UEIP)        
        PORT = Controller.DeviceName
        self.__super.__init__(**filter_dict(locals(), self.Arguments))

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        Controller = Ident ('Underlying controller', MotorController),
        ADDR       = Simple('Address on controller', str),
        P          = Simple('Device Prefix', str),
        M          = Simple('Device Suffix', str),
        DESC       = Simple('Description (displayed on edm screen)', str),
        MRES       = Simple('Motor Step Size (EGU)', str),
        gda_name   = Simple('GDA Name', str),
        gda_desc   = Simple('GDA description', str),
        DTYP       = Simple('DTYP of record', str),
        DIR        = Simple('User Direction', int),
        VBAS       = Simple('Base Velocity (EGU/s)', float),
        VELO       = Simple('Velocity (EGU/s)', float),
        VMAX       = Simple('Max Velocity (EGU/s), defaults to VELO', float),
        ACCL       = Simple('Seconds to Velocity', float),
        BDST       = Simple('BL Distance (EGU)', float),
        BVEL       = Simple('BL Velocity (EGU/s)', float),
        BACC       = Simple('BL Seconds to Veloc.', float),
        PREC       = Simple('Display Precision', int),
        EGU        = Simple('Engineering Units', str),
        DHLM       = Simple('Dial High Limit', float),
        DLLM       = Simple('Dial Low Limit', float),
        HLSV       = Sevr  ('HW Lim. Violation Svr'),
        INIT       = Simple('Startup commands', str),
        SREV       = Simple('Steps per Revolution', int),
        RRES       = Simple('Readback Step Size (EGU)', float),
        TWV        = Simple('Tweak Step Size (EGU)', float),
        ERES       = Simple('Encoder Step Size (EGU)', float),
        JAR        = Simple('Jog Acceleration (EGU/s^2)', float),
        UEIP       = Simple('Use Encoder If Present', bool),
        OFF        = Simple('User Offset (EGU)', float),
        RDBD       = Simple('Retry Deadband (EGU)', float),
        FOFF       = Simple('Freeze Offset, 0=variable, 1=frozen', int))

    # Substitution attributes
    TemplateFile = 'basic_asyn_motor.template'
    Arguments = ['PORT'] + ArgInfo.Names(without = ['Controller'])

#    IdenticalSim = True  
#    EdmEmbedded = ("motor-embed-small.edl","motor=%(P)s%(M)s,filename=motor.edl")    
#    EdmScreen = ("motor.edl","motor=%(P)s%(M)s")
#    StatusPv = "%(P)s%(M)s.MOVN"
#    SevrPv = StatusPv        
                        

class motorUtil(Substitution, Device):
    '''Status record for Stop all and motors moving'''

    def __init__(self, P):
        self.P = P
        self.__super.__init__(P = P)
    
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P = Simple('Device Prefix', str))
        
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'motorUtil.template'
#    IdenticalSim = True  

    def Initialise(self):
        print 'motorUtilInit("%(P)s")' % self.__dict__
