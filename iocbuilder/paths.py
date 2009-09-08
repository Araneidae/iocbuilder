# Configurable paths.
import os

EPICS_HOST_ARCH = 'linux-x86'
EPICS_HOST_ARCH = os.environ.get('EPICS_HOST_ARCH', EPICS_HOST_ARCH)

DLS_EPICS_VERSION = 'R3.14.8.2'
DLS_EPICS_VERSION = os.environ.get('DLS_EPICS_VERSION', DLS_EPICS_VERSION)

EPICS_BASE = '/dls_sw/epics/%s/base' % DLS_EPICS_VERSION
EPICS_BASE = os.environ.get('EPICS_BASE', EPICS_BASE)

# Where the msi application is located.
msiPath = '/dls_sw/epics/%s/extensions/bin/%s' % (
    DLS_EPICS_VERSION, EPICS_HOST_ARCH)
# Where modules are located.
module_path = '/dls_sw/prod/%s/support' % DLS_EPICS_VERSION
