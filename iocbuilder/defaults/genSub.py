from iocbuilder import Device

__all__ = ['genSub']

class GenSub(Device):
    '''Implementation of gensub record type.'''
    LibFileList = ['genSub']
    DbdFileList = ['genSubRecord']
    AutoInstantiate = True

# For backwards compatibility
genSub = GenSub
