from iocbuilder import Device
from iocbuilder.hardware import AutoProtocol

__all__ = ['HostLink']

class HostLink(Device, AutoProtocol):
    '''HostLink module'''
    LibFileList = ['HostLink']
    DbdFileList = ['HostLink']
    ProtocolFiles = ['Hostlink.proto']
    AutoInstantiate = True
