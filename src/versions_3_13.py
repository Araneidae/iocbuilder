# Version information for EPICS 3.13

SetModulePath('/home/diamond/R3.13.9/prod/support')
# Nasty hack: required for mixed build process!
ModuleVersion('EPICS_BASE',
    home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)
ModuleVersion('baseTop',      '3-2')

Configure(
    baselib = hardware.baselib.iocBase,
    dynamic_load = True,
    register_dbd = False,
    version = '3_13',
    architecture = 'ppc604')
