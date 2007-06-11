# Version information for EPICS 3.14.8.2: static build only

SetModulePath('/dls_sw/prod/R3.14.8.2/support')
ModuleVersion('EPICS_BASE',
    home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)

Configure(
    baselib = hardware.baselib.epicsBase,
    dynamic_load = False,
    register_dbd = True,
    version = '3_14',
    architecture = 'vxWorks-ppc604_long')

