from iocbuilder import Substitution
from iocbuilder.hardware import AutoProtocol

__all__ = ['NSC200']

class NSC200(Substitution, AutoProtocol):
    Arguments = ['P', 'M', 'CH', 'PORT']
    TemplateFile = 'NSC200.template'
    ProtocolFiles = ['NSC200.proto']
