# Version information for EPICS 3.14.8.2: static build only

SetModulePath('/dls_sw/prod/R3.14.8.2/support')
ModuleVersion('EPICS_BASE',
    home = '/dls_sw/epics/R3.14.8.2/base', use_name = False)


ModuleVersion('genSub',         '1-6dls2-5')
ModuleVersion('autosave',       '4-2-1dls1')
ModuleVersion('calc',           '2-6-1dls1')
ModuleVersion('ipac',           '2-8dls4-3')
ModuleVersion('DLS8512',        '2-7')
ModuleVersion('Hy8401ip',       '3-4')
ModuleVersion('Hy8402ip',       '3-6')
ModuleVersion('Hy8515',         '3-4')
ModuleVersion('Hy8513',         '1-1')
ModuleVersion('Timing',         '2-1')
ModuleVersion('TimingTemplates','3-0')
ModuleVersion('cmsIon',         '2-4')
ModuleVersion('streamDevice',   '2-2')
ModuleVersion('sscan',          '2-5-2dls1')
ModuleVersion('asyn',           '4-6')
ModuleVersion('motor',          '6-0dls8')

ModuleVersion('Mr1394',  '1-8')
ModuleVersion('vxStats', '1-10')
ModuleVersion('IOCinfo', '2-7')

ModuleVersion('diagTools', home='/home/mga83/epics/Diagnostics')


Configure(
    baselib = hardware.baselib.epicsBase,
    dynamic_load = False,
    register_dbd = True,
    version = '3_14',
    architecture = 'vxWorks-ppc604_long')

