# Version information for EPICS 3.14.6.
# This version file is for backwards compatibility only

SetModulePath('/home/diamond/R3.14.6/prod/support')
# Note that the epics base below is for 3.14.8.2: this is a hack required for
# the makefile system.  
ModuleVersion('EPICS_BASE',
    home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)
ModuleVersion('baseTop', '4-0')

Configure(
    baselib = hardware.baselib.iocBase,
    dynamic_load = True,
    register_dbd = True,
    version = '3_14_6',
    architecture = 'vxWorks-ppc604_long')

