# Version information for EPICS 3.13

SetModulePath('/home/diamond/R3.13.9/prod/support')


# Nasty hack: required for mixed build process!
ModuleVersion('EPICS_BASE',
    home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)


# Base library
ModuleVersion('baseTop',      '3-2')
ModuleVersion('autosave',     '1-0')

# Custom record types
ModuleVersion('gensub',       '2-3')
ModuleVersion('transform',    '1-1')
ModuleVersion('mbbi32Direct', '1-0')

# Support libraries
ModuleVersion('streamDevice', '3-2')
ModuleVersion('vxStats',      '1-5')

# Real hardware
ModuleVersion('ipac',         '3-5')
ModuleVersion('Hy8401ip',     '3-4')
ModuleVersion('Hy8402ip',     '2-0')    # --- now 3-5, considerably changed.
ModuleVersion('DLS8512',      '2-4')    # --- now 2-6 !
ModuleVersion('Hy8513',       '1-0')
ModuleVersion('Hy8515',       '3-3')    # --- now 3-6 !
ModuleVersion('Hy8505',       '1-1dls1-0')
ModuleVersion('motor',        '4-3')
ModuleVersion('Timing',       '1-62')
ModuleVersion('TimingTemplates', '2-45')

# Local version information.  

# The diagTools library supplies support for a variety of components.
ModuleVersion('diagTools',    '1-7')

# The cmsIon directory is used to define support for the health physics
# radiation safety monitors.
ModuleVersion('cmsIon',       '2-3')
# The IOCinfo library provides temperature information
ModuleVersion('IOCinfo',      '2-7')


Configure(
    baselib = hardware.baselib.iocBase,
    dynamic_load = True,
    register_dbd = False,
    version = '3_13',
    architecture = 'ppc604')
