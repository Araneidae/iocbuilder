from iocbuilder import Device, ModuleBase, SetSimulation
from iocbuilder.arginfo import *

# Don't do anything if not in simulation mode
class serial_sim_instance(Device):
    IPCurrent = 8001
    IPUsed = set()
    def __init__(self, name, pyCls, module, IPPort = None, debug = None, args=""):
        self.__dict__.update(locals())
        self.IP = IPPort
        self.__super.__init__()
    
    def startIP(self):
        if self.IP is None:
            while serial_sim_instance.IPCurrent in self.IPUsed:
                serial_sim_instance.IPCurrent += 1            
            self.IP = serial_sim_instance.IPCurrent
        self.IPUsed.add(self.IP)
        return "localhost:%d" % self.IP
        
    def startSerial(self):
        self.Serial = "$(%s)" % self.name
        return self.Serial        

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        name   = Simple('Object name', str),
        pyCls  = Simple('Class name of python serial_sim subclass', str),
        module = Simple('Python module (filename) to import cls from', str),                        
        IPPort = Simple('If specified, use this IP port number, otherwise choose the first availble one starting from 8001', int),        
        debug  = Simple('If specified, run a debug port. You should start from 9001 to avoid clashes', int),
        args   = Simple('Args string to pass to the cls init. You don\'t need to quote it', str))

class serial_sim_instance_sim(serial_sim_instance):
    '''Creates a serial_sim instance'''       

    # Device attributes
    LibFileList = ['pyDrv']
    DbdFileList = ['pyDrv']    

    def InitialiseOnce(self):
        print '# Setup pythonpaths for simulations'
        print 'epicsEnvSet("PYTHONHOME", "/dls_sw/tools/python2.4")'
        print 'epicsEnvSet("PYTHONPATH", "$(STREAM_PROTOCOL_PATH)")'

    def Initialise(self):
        print 'Python("from %(module)s import %(pyCls)s")' % self.__dict__
        print 'Python("%(name)s = %(pyCls)s(%(args)s)")' % self.__dict__
        if hasattr(self, "IP"):
            print 'Python("%(name)s.start_ip(%(IP)s)")' % self.__dict__
        if hasattr(self, "Serial"):
            print 'Python("%(name)s.start_serial(%(Serial)s)")' % self.__dict__
        if self.debug is not None:
            print 'Python("%(name)s.start_debug(%(debug)s)")' % self.__dict__            

SetSimulation(serial_sim_instance, serial_sim_instance_sim)
