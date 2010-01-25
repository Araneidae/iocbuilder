from iocbuilder import AutoSubstitution
from iocbuilder.modules.streamDevice import AutoProtocol

class eurotherm2k(AutoSubstitution, AutoProtocol):
    '''Controls a eurotherm 2000 series temperature controller'''

    ## Parse this template file for macros
    TemplateFile = 'eurotherm2k.template'

    ## This is the streamDevice protocol file to use
    ProtocolFiles = ['eurotherm2k.proto']


