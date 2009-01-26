from iocbuilder import Device

__all__ = ['genSub']

class genSub(Device):
    '''Implementation of gensub record type.'''
    LibFileList = ['genSub']
    DbdFileList = ['genSubRecord']
    AutoInstantiate = True
