from iocbuilder import Substitution, hardware

__all__ = ['cmsIon']


class cmsIon(Substitution):
    Arguments = ('device', 'port', 'high', 'hihi')
    TemplateFile   = 'cmsIon-v1.template'

    def __init__(self, serialCard, domain, id, socket, high, hihi):
        '''Creates support for radiation safety monitoring system.  The
        arguments are:
            domain is the machine location (LI/BRnnC/SRnnC),
            id is the sequence number (normally 1),
            socket is the connector number on the PIM used to connect to the
                serial device (with the first socket numbered 1).
        '''
        port = serialCard.channel(socket-1)
        stream = hardware.streamProtocol_v1(port,
            self.ModuleFile('data/cmsIon-v1.protocol'))
        self.__super.__init__(
            device = '%s-RS-RDMON-%02d' % (domain, id),
            port = stream.port,
            high = high, hihi = hihi)
