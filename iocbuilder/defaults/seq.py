from iocbuilder import Device

__all__ = ['Seq']


class Seq(Device):
    LibFileList = ['seq', 'pv']

    def __init__(self):
        '''Not supported yet.'''
        assert False, 'Don\'t create instances of Seq until it works!'
