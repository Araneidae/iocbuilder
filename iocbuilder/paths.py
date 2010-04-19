# Configurable paths.
import os


def ValidateEpicsBase(epics_base):
    '''Very DLS specific validation and normalisation of EPICS_BASE.'''
    path = epics_base.split('/')
    if path[-1] == '':
        del path[-1]
    assert len(path) == 5 and \
        '/'.join(path[:3]) == '/dls_sw/epics' and \
        path[4] == 'base', 'Invalid DLS EPICS_BASE: "%s"' % epics_base
    return '/'.join(path)

def GetModulePath():
    '''Very DLS specific computation of module path from EPICS_BASE.'''
    return '/dls_sw/prod/%s/support' % EPICS_BASE.split('/')[3]

def GetMsiPath():
    '''Very DLS specific computation of path to msi.'''
    return '%s/extensions/bin/%s' % (
        '/'.join(EPICS_BASE.split('/')[:-1]), EPICS_HOST_ARCH)


def SetEpicsBase(epics_base):
    '''Can be called to override the computed EPICS_BASE and other settings.
    If called late then must be called before any of the paths are used!'''

    global EPICS_BASE, msiPath, module_path

    EPICS_BASE = ValidateEpicsBase(epics_base)
    module_path = GetModulePath()
    msiPath = GetMsiPath()

    print 'paths.EPICS_BASE =', EPICS_BASE



EPICS_HOST_ARCH = 'linux-x86'
EPICS_HOST_ARCH = os.environ.get('EPICS_HOST_ARCH', EPICS_HOST_ARCH)

# If EPICS_BASE has been set in the environment set this version by default.
# This can be overridden subsequently by another call to SetEpicsBase.
if 'EPICS_BASE' in os.environ:
    SetEpicsBase(os.environ['EPICS_BASE'])
