from iocbuilder import Device
from iocbuilder.arginfo import *

from iocbuilder.modules.asyn import AsynPort, Asyn, AsynIP
from iocbuilder.modules.motor import MotorLib, MotorController
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
#    EdmScreen = ('dls-motor-control.py -o tcpip -s %(Server)s -p %(Port)s', '')
    
    def __init__(self, DeviceName, IP, PortName = None, NAxes = 8, 
        IdlePoll = 500, MovingPoll = 50):
        # First create an asyn IP port to connect to
        if PortName is None:
            PortName = DeviceName + 'port'        
        if ":" not in IP:
            IP = IP + ':1025'            
        self.IPPort = AsynIP(IP, IPPort)
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
    
#    def getPmc(self):
#        if not hasattr(self,"pmc"):
#            self.pmc = IocDataStream(self.DeviceName+".pmc",path="pmc")    
#        return self.pmc        

#    def IncludePmc(self,filename,macrodict={}):
#        text = open(filename).read()
#        for k,v in macrodict.items():
#            text = text.replace("$(%s)"%k,"%s"%v)
#        self.getPmc().write(text)
                    
    def Initialise(self):
        print 'pmacAsynMotorCreate("%(PortName)s", 0, %(Card)d, %(NAxes)d)'\
            %self.__dict__
        print 'drvAsynMotorConfigure("%s", "pmacAsynMotor", %d, %d)'%(
            self.DeviceName(), self.Card, self.NAxes+1)            
        print 'pmacSetIdlePollPeriod(%(Card)d, %(IdlePoll)d)'%self.__dict__
        print 'pmacSetMovingPollPeriod(%(Card)d, %(MovingPoll)d)'%self.__dict__

'''
class GeoBrick_sim(GeoBrick):
    Dependencies = (MotorSimLib,)

    def InitialiseOnce(self):
        print 'motorSimCreate( 100, 0, -150000, 150000, 3, %d, %d )'\
            %(len(self._Cards),self.NAxes+1)

    def Initialise(self):
        print 'drvAsynMotorConfigure("%s", "motorSim", %d, %d)'%(
            self.DeviceName, self.Card+100, 
            self.NAxes+1)            
'''
                  
class CS(Device):
    Dependencies = (tpmac,)
    LibFileList = [ "pmacAsynCoord" ]
    DbdFileList = [ "pmacAsynCoord" ]
    _CSs = []
       
    def __init__(self, DeviceName, Controller, CS, PLCNum = None, NAxes = 9, 
        Program = 10, IdlePoll = 500, MovingPoll = 100):

        self.PortName = Controller.DeviceName()
        # PLC number for position reporting
        if PLCNum is None:
            self.PLCNum = CS + 15        
        else:
            self.PLCNum = PLCNum
        # reference for linking pmacAsynCoordCreate and drvAsynMotorConfigure
        Ref = len(self._CSs)
        self._CSs.append(self)       
        # Store other attributes
        self.NAxes = NAxes
        self.IdlePoll = IdlePoll
        self.MovingPoll = MovingPoll  
        self.Program = Program
        self.__super.__init__()

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
        print 'pmacAsynCoordCreate("%(PortName)s", 0, %(CS)d, %(Ref)d, '\
            '%(Program)s)'%self.__dict__
        print 'drvAsynMotorConfigure("%(DeviceName)s", "pmacAsynCoord", '\
            '%(Ref)d, %(NAxes)d)'%self.__dict__
        print 'pmacSetCoordIdlePollPeriod(%(Ref)d, %(IdlePoll)d)'%self.__dict__
        print 'pmacSetCoordMovingPollPeriod(%(Ref)d, %(MovingPoll)d)'%self.__dict__
'''
class CS_sim(CS):
    Dependencies = (MotorSimLib,)
    
    def InitialiseOnce(self):
        print 'motorSimCreate( 200, 0, -150000, 150000, 3, %d, %d )'\
            %(len(self._CSs),self.NAxes+1)

    def Initialise(self):
        print 'drvAsynMotorConfigure("%s", "motorSim", %d, %d)'%(
            self.DeviceName, self.Ref+200, self.NAxes)  
'''
