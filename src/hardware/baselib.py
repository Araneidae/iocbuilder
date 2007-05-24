# ----------------------------------------------------------------------
#   Generic library support: iocBase, ipacLib and others

import os.path

from _epics import *

# These devices are used directly, while the others are loaded as part of
# other devices
__all__ = ['vxStats', 'mbbi32Direct', 'genSub', 'Transform']




# The iocBase library must be loaded first before all other libraries.
# This loads the core files used to make up an EPICS IOC.
#
# We take the opportunity to generate some useful early IOC initialisation
# code at the same time.
class iocBase(Device):
    '''Core IOC library (for 3.13 and 3.14.6 only).  This library should be
    loaded before anything else is loaded.'''

    ModuleName = 'baseTop'

    LibFileList = ['iocCore', 'baseLib', 'initHooks.o']
    DbdFileList = ['baseApp.dbd']

    LibFileList__3_14_6 = ['baseTop.munch']
    DbdFileList__3_14_6 = ['baseTop.dbd']

    def SetIocName(self, ioc_name):
        pass


class epicsBase(Device):
    '''EPICS base library (for 3.14 only).  This should be loaded first.'''
    ModuleName = 'EPICS_BASE'

    DbdFileList = ['base.dbd']

    # This *must* initialise before anything else!
    InitialisationPhase = Device.FIRST

    def SetIocName(self, ioc_name):
        self.ioc_name = ioc_name

    def InitialiseOnce(self):
        dbd_name = self.ioc_name
        print 'cd homeDir'
        print 'ld < bin/%s/%s.munch' % (self.Arch(), self.ioc_name)
        print 'dbLoadDatabase "dbd/%s.dbd"' % dbd_name
        print '%s_registerRecordDeviceDriver(pdbbase)'% \
            dbd_name.replace('-', '_')


def EpicsBasePath():
    return epicsBase.LibPath()

        

class mbbi32Direct(Device):
    '''Implementation of mbbi32Direct record type.'''
    
    LibFileList = ['mbbi32DirectRecord.o']
    DbdFileList = ['mbbi32Direct.dbd']


class genSub(Device):
    '''Implementation of gensub record type.'''

    ModuleName__3_13 = 'gensub'
    
    LibFileList = ['genSubRecord.o']
    DbdFileList = ['menuGenSub.dbd', 'genSubRecord.dbd']

    LibFileList__3_14 = ['genSub']
    DbdFileList__3_14 = ['genSubRecord.dbd']
    

class Sscan(Device):
    ModuleName = 'sscan'

    LibFileList = ['sscan']
    DbdFileList = ['sscanSupport.dbd']


class Transform(Device):
    '''Implementation of transform record type.'''

    ModuleName = 'transform'

    LibFileList = ['transformLib']
    DbdFileList = ['transformApp.dbd']

    ModuleName__3_14 = 'calc'
    Dependencies__3_14 = (Sscan,)
    LibFileList__3_14 = ['calc']
    DbdFileList__3_14 = ['calcSupport.dbd']
    

class vxStats(Substitution, Device):
    '''Creates vx statistics for the ioc.  To view the ioc statistics
    run vxStatsApp/opi/edl/iocStatus.edl with the same device=iocname
    substitution.'''

    Arguments = ('device',)
    TemplateFile = 'vxStats.template'
    
    LibFileList = ['vxStatsLib']
    DbdFileList = ['vxStats.dbd']

    def __init__(self, iocname):
        '''Creates a vxStats expansion instance for the named ioc.'''
        # This had better delegate to Substitution, otherwise the arguments
        # are going to go astray!  Thus the class inheritance order matters.
        self.__super.__init__(device = iocname)
