from iocbuilder import Substitution, ModuleBase, records
from iocbuilder import SetSimulation, DummySimulation
from iocbuilder.arginfo import *

from iocbuilder.modules.HostLink import HostLink
from iocbuilder.modules.busy import Busy
from iocbuilder.modules.asyn import AsynOctetInterface


class vacuumValveRead(Substitution):
    Dependencies = (HostLink,)
        
    # __init__ arguments
    ArgInfo = makeArgInfo( 
        device = Simple('Device Prefix', str),
        port   = Ident ('Asyn Serial Port', AsynOctetInterface))
        
    # Substitution attributes
    Arguments = ArgInfo.Names()
    TemplateFile = 'vacuumValveRead.template'   


# Simulation is just a placeholder to satisfy vacuumValve_callback
class vacuumValveRead_sim(DummySimulation): pass
SetSimulation(vacuumValveRead, vacuumValveRead_sim)


class valve(ModuleBase):
    pass
    
class externalValve(valve):
    def __init__(self, device):
        self.args = dict(device = device)
        self.__super.__init__()
        
    ArgInfo = makeArgInfo(__init__,
        device = Simple ('Device macro of valve that exists in another IOC', 
            str))

class vacuumValve_callback(Substitution, valve):
    Dependencies = (Busy,)
    
    # get the device and port from the vacuumValveRead object, then
    # init            
    def __init__(self, device, crate, valve, desc = None, ilks = [''], 
            gilks = [''], name = '', gda = False):  
        if desc is None:
            desc = device
        if gda:
            gda_name, gda_desc = (name, desc)
        else:
            gda_name, gda_desc = ('', '')            
        kwargs = dict(
            zip(self.ilkNames, (ilks + ['']*16)[:16]) + \
            zip(self.gilkNames, (gilks+ ['']*16)[:16]),         
            device = device,
            name = name,
            desc = desc,
            vlvcc = crate.args['device'],
            port = crate.args['port'], 
            valve = '%02d' % valve,         
            gda_name = gda_name,
            gda_desc = gda_desc,            
        )
        self.__super.__init__(**kwargs)

    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        device   = Simple('Device Prefix', str),
        crate    = Ident ('Parent vacuumValveRead object', vacuumValveRead),
        valve    = Simple('Valve number (1 to 6) in PLC', int),
        desc     = Simple('Description for label, defaults to $(device)', str),
        ilks     = List  ('Interlock Descriptions', 16, Simple, str),
        gilks    = List  ('Gauge Interlock Descriptions', 16, Simple, str),
        name     = Simple('Object name, also used for gda name if gda', str),
        gda      = Simple('Set to True to make available to gda', bool))

    # Substitution attributes      
    ilkNames = ['ilk%s'%i for i in range(16)]
    gilkNames = ['gilk%s'%i for i in range(16)]    
    Arguments = ['name', 'device', 'desc', 'vlvcc', 'port', 'valve', 
        'gda_name', 'gda_desc'] + ilkNames + gilkNames
    TemplateFile = 'vacuumValve_callback.template'
    

# Simulation has different db file
class vacuumValve_callback_sim(vacuumValve_callback):
    TemplateFile = 'simulation_vacuumValve_callback.template'
SetSimulation(vacuumValve_callback, vacuumValve_callback_sim)


class vacuumValveGroup(Substitution):
    Arguments = (
        'device', 'delay',
        'valve1', 'valve2', 'valve3', 'valve4',
        'valve5', 'valve6', 'valve7', 'valve8')
    TemplateFile = 'vacuumValveGroup.template'

class dummyValve(Substitution):
    Arguments = ('device',)
    TemplateFile = 'dummyValve.template'

class BeamRecords(ModuleBase):
    '''Creates beam records that the gui can connect to to see which valves and
    shutters are open'''
    
    def __init__(self, P, objects = [None]):
        # make a list of objects
        obs = [ o for o in objects if o is not None ]
        # now get their status pvs
        pvs = [ '%s:STA CP' % o.args['device'] for o in obs ]
        # now find out which calc input they should be
        letters = [ chr(65+j) for j in range(len(pvs)) ]
        # and what the input link should be
        inps = [ 'INP%s' % x for x in letters ]
        # zip them together
        zipped = zip(inps, pvs)
        for i in range(1,len(zipped)+1):        
            recordName = '%s:STA%s' % (P, i)
            inpdict = dict(zipped[:i])
            CALC = '&'.join(['%s=1'%l for l in letters[:i]])
            records.calc(recordName, CALC=CALC, **inpdict)
        self.__super.__init__()        
                
    # __init__ arguments
    ArgInfo = makeArgInfo(__init__,
        P = Simple('Device prefix for summary PV, records will be '
                   '$(P):STA$(N) for 1<=N<=#objects', str),
        objects = List('vacuumValve object', 12, Ident, valve))
    
