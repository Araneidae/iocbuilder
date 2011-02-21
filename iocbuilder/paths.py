'''Configurable paths.'''

## IOC builder path configuration.
#
# This file defines the following symbols need to locate EPICS resources:
#
#   EPICS_BASE
#       This must be set, and defines the absolute path to the built EPICS
#       installation that will be used to generate the IOCs.  This value
#       can be picked up from the calling environment, or can be overridden
#       in a Configure() call.
#
#   EPICS_HOST_ARCH
#       This must be set: it is used to load the dbd reading library.  The
#       default value of linux-x86 can be overridden in the environment.
#
#   module_path
#       This variable is used to default the module home directory in
#       ModuleVersion() calls, so strictly speaking is optional if the
#       default is not needed.
#
#   msiPath
#       This is used to compute the location of the msi executable.  This is
#       optional if msi is on the path.

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

def _GetEpicsVersion(epics_base):
    '''Very DLS specific extraction of EPICS version from epics_base.'''
    epics_base = epics_base.split('/')
    # Try to recognise standard form:
    #   /dls_sw/epics/$EPICS_RELEASE/base
    if epics_base[-1] == '':
        del epics_base[-1]
    if '/'.join(epics_base[:3] + epics_base[4:]) == '/dls_sw/epics/base':
        return epics_base[3]
    else:
        return None

def _GetModulePath(epics_version):
    '''Very DLS specific computation of module path from EPICS_BASE.'''
    return '/dls_sw/prod/%s/support' % epics_version

def _GetModuleWorkPath(epics_version):
    '''Very DLS specific computation of module path from EPICS_BASE.'''
    return '/dls_sw/work/%s/support' % epics_version

def _GetMsiPath(epics_version):
    '''Very DLS specific computation of path to msi.'''
    return '/dls_sw/epics/%s/extensions/bin/%s' % (
        epics_version, EPICS_HOST_ARCH)


# Can be called to override the computed EPICS_BASE and other settings.
# If called late then must be called before any of the paths are used!
def SetEpicsBase(epics_base):
    global EPICS_BASE, msiPath, module_path, module_work_path

    EPICS_BASE = epics_base
    epics_version = _GetEpicsVersion(epics_base)
    if epics_version:
        module_path = _GetModulePath(epics_version)
        module_work_path = _GetModuleWorkPath(epics_version)
        msiPath = _GetMsiPath(epics_version)



EPICS_HOST_ARCH = 'linux-x86'
EPICS_HOST_ARCH = os.environ.get('EPICS_HOST_ARCH', EPICS_HOST_ARCH)

# Default values if values cannot be set.
module_path = None
msiPath = None

# If EPICS_BASE has been set in the environment set this version by default.
# This can be overridden subsequently by another call to SetEpicsBase.
if 'EPICS_BASE' in os.environ:
    SetEpicsBase(os.environ['EPICS_BASE'])
