from iocbuilder import Device, SetSimulation, IocDataStream, iocwriter
from iocbuilder.arginfo import *

from iocbuilder.modules.asyn import AsynPort, Asyn
from iocbuilder.modules.motor import MotorLib, MotorController, MotorSimLib
import sys 

PMAC = 0
GEOBRICK = 1

class tpmac(Device):
    Dependencies = (Asyn,MotorLib)
    AutoInstantiate = True  

class DeltaTau(AsynPort, MotorController):
    Dependencies = (tpmac,)        

class GeoBrick(DeltaTau):
    ctype = GEOBRICK
    LibFileList = [ "pmacAsynIPPort", "pmacAsynMotor" ]
    DbdFileList = [ "pmacAsynIPPort", "pmacAsynMotor" ]    
    _Cards = []
    
    def __init__(self, DeviceName, IP, PortName = None, NAxes = 8, 
        IdlePoll = 500, MovingPoll = 50):
        # First create an asyn IP port to connect to
        if PortName is None:
            PortName = DeviceName + 'port'        
        if ":" not in IP:
            IP = IP + ':1025'            
        self.IP = IP
        self.PortName = PortName
        # Now add self to list of cards
        self.Card = len(self._Cards)
        self._Cards.append(self)        
        # Store other attributes
        self.NAxes = NAxes
        self.IdlePoll = IdlePoll
        self.MovingPoll = MovingPoll
        # init the AsynPort superclass
        self.__super.__init__(DeviceName)
    
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        DeviceName = Simple('Name to use for the asyn port', str),
        IP         = Simple('IP address of the geobrick', str),
        PortName   = Simple('Port Name, defaults to DeviceName+"port"', str),
        NAxes      = Simple('Number of axes', int),
        IdlePoll   = Simple('Idle Poll Period in ms', int),
        MovingPoll = Simple('Moving Poll Period in ms', int))
    
    def IncludePmc(self,filename,macrodict={}):
        if not hasattr(self,"pmc"):
            self.pmc = IocDataStream(self.DeviceName()+".substitutions")
            iocwriter.pmcs.append(self.DeviceName()+".substitutions")
        if not macrodict:
            macrodict = dict(x = "x")
        self.pmc.write("file %s\n{ pattern\n{" % filename)
        keys = []
        values = []
        for k in sorted(macrodict.keys()):
            keys.append(k)
            values.append('"%s"' % macrodict[k])
        self.pmc.write(", ".join(keys)+"}\n{")
        self.pmc.write(", ".join(values)+"}\n}\n\n")        
                    
    def Initialise(self):
        print '# Create IP Port (IPPort, IPAddr)'    
        print 'pmacAsynIPConfigure("%(PortName)s", "%(IP)s")'\
            %self.__dict__
        print '# Create GeoBrick (IPPort, Addr, BrickNum, NAxes)'    
        print 'pmacAsynMotorCreate("%(PortName)s", 0, %(Card)d, %(NAxes)d)'\
            %self.__dict__
        print '# Configure GeoBrick (PortName, DriverName, BrickNum, NAxes+1)'            
        print 'drvAsynMotorConfigure("%s", "pmacAsynMotor", %d, %d)'%(
            self.DeviceName(), self.Card, self.NAxes+1)            
        print 'pmacSetIdlePollPeriod(%(Card)d, %(IdlePoll)d)'%self.__dict__
        print 'pmacSetMovingPollPeriod(%(Card)d, %(MovingPoll)d)'%self.__dict__


class GeoBrick_sim(GeoBrick):
    Dependencies = (MotorSimLib,)

    def InitialiseOnce(self):
        print 'motorSimCreate( 100, 0, -150000, 150000, 3, %d, %d )'\
            %(len(self._Cards),self.NAxes+1)

    def Initialise(self):
        print 'drvAsynMotorConfigure("%s", "motorSim", %d, %d)'%(
            self.DeviceName(), self.Card+100, 
            self.NAxes+1)            
SetSimulation(GeoBrick, GeoBrick_sim)
                  
class CS(DeltaTau):
    Dependencies = (tpmac,)
    LibFileList = [ "pmacAsynCoord" ]
    DbdFileList = [ "pmacAsynCoord" ]
    _CSs = []
       
    def __init__(self, DeviceName, Controller, CS, PLCNum = None, NAxes = 9, 
        Program = 10, IdlePoll = 500, MovingPoll = 100):

        self.PortName = Controller.PortName
        self.IncludePmc = Controller.IncludePmc
        # PLC number for position reporting
        if PLCNum is None:
            self.PLCNum = CS + 15        
        else:
            self.PLCNum = PLCNum
        # reference for linking pmacAsynCoordCreate and drvAsynMotorConfigure
        self.Ref = len(self._CSs)
        self._CSs.append(self)       
        # Store other attributes
        self.NAxes = NAxes
        self.IdlePoll = IdlePoll
        self.MovingPoll = MovingPoll  
        self.Program = Program
        self.CS = CS
        # init the AsynPort superclass
        self.__super.__init__(DeviceName) 
     
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        DeviceName = Simple('CS Name (for asyn port that motor records are connected to)', str),
        Controller = Ident ('Underlying PMAC or GeoBrick object', DeltaTau),
        CS         = Simple('CS number', int),
        PLCNum     = Simple('PLC Number, defaults to CS + 15', int),
        NAxes      = Simple('Number of axes', int),
        Program    = Simple('Motion Program to run', int),
        IdlePoll   = Simple('Idle Poll Period in ms', int),
        MovingPoll = Simple('Moving Poll Period in ms', int))

    def Initialise(self):
        print '# Create CS (ControllerPort, Addr, CSNumber, CSRef, Prog)'
        print 'pmacAsynCoordCreate("%(PortName)s", 0, %(CS)d, %(Ref)d, '\
            '%(Program)s)'%self.__dict__
        print '# Configure CS (PortName, DriverName, CSRef, NAxes)'
        print 'drvAsynMotorConfigure("%s", "pmacAsynCoord", %d, %d)'%(
            self.DeviceName(), self.Ref, self.NAxes)                 
        print '# Set Idle and Moving poll periods (CS_Ref, PeriodMilliSeconds)'
        print 'pmacSetCoordIdlePollPeriod(%(Ref)d, %(IdlePoll)d)'%self.__dict__
        print 'pmacSetCoordMovingPollPeriod(%(Ref)d, %(MovingPoll)d)'%self.__dict__

class CS_sim(CS):
    Dependencies = (MotorSimLib,)
    
    def InitialiseOnce(self):
        print 'motorSimCreate( 200, 0, -150000, 150000, 3, %d, %d )'\
            %(len(self._CSs),self.NAxes+1)

    def Initialise(self):
        print 'drvAsynMotorConfigure("%s", "motorSim", %d, %d)'%(
            self.DeviceName(), self.Ref+200, self.NAxes)  
SetSimulation(CS, CS_sim)
