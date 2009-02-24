from iocbuilder import Substitution, hardware
from iocbuilder.hardware import streamDeviceVersion, AutoProtocol

__all__ = ['cmsIon']


class cmsIon(Substitution, AutoProtocol):
    # __init__ arguments
    ArgInfo = [
        ('device', str, 'Device Prefix'),
        ('port', None, 'Asyn port'),
        ('high', int, 'Integrated dose (since reset) HIGH value', 50),
        ('hihi', int, 'Integrated dose (since reset) HIHI value', 100)        
    ]    
    XMLObjects = ['port']    
    # Substitution attributes        
    if streamDeviceVersion == 1:
        TemplateFile  = 'cmsIon-v1.template'
        ProtocolFiles = ['cmsIon-v1.protocol']
    else:
        TemplateFile  = 'cmsIon.template'
        ProtocolFiles = ['cmsIon.protocol']
    

    def __init__(self, port, **kwargs):
        '''Creates support for radiation safety monitoring system.'''
        # need this line so that stream v1 works
        stream = hardware.streamProtocol(port, self.Protocols[0])
        self.__super.__init__(port = stream.port, **kwargs)

        
def createCmsIon(serialCard, domain, id, socket, high, hihi):
    '''Helper routine for creating cmsIon instances.  The  arguments are:
        domain is the machine location (LI/BRnnC/SRnnC/etc),
        id is the sequence number (normally 1),
        socket is the connector number on the PIM used to connect to the
            serial device (with the first socket numbered 1).'''
    port = serialCard.channel(socket - 1)
    if streamDeviceVersion > 1:
        port = hardware.AsynSerial(port)
    return cmsIon(
        device = '%s-RS-RDMON-%02d' % (domain, id),
        port = port, high = high, hihi = hihi)
