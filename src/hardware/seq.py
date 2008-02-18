from _epics import *

__all__ = ['Seq']


class Seq(Device):
    ModuleName = 'seq'

    LibFileList = ['seq', 'pv']

    def __init__(self):
        '''Not supported yet.'''
        assert False, 'Don\'t create instances of Seq until it works!'
