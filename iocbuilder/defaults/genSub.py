from iocbuilder import Device

__all__ = ['GenSub']

class GenSub(Device):
    '''Implementation of gensub record type.'''
    LibFileList = ['genSub']
    DbdFileList = ['genSubRecord']
    AutoInstantiate = True
