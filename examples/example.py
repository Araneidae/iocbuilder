import sys
import os
sys.path.append(
    os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
# from pkg_resources import require
# require('iocbuilder')
import iocbuilder

iocbuilder.ConfigureIOC()

from iocbuilder import ModuleVersion, WriteIoc
from iocbuilder import hardware

ModuleVersion('ipac',           '2-8dls4-3')
ModuleVersion('Hy8515',         '3-7')
ModuleVersion('asyn',           '4-9')
ModuleVersion('streamDevice',   '2-4dls2')
ModuleVersion('newstep',        '1-3',  load_path = 'defaults')
ModuleVersion('cmsIon',         '2-10')

card4 = hardware.Hy8002(4)
serial1 = card4.Hy8515(0)

for ch in range(8):
    asyn = hardware.AsynSerial(serial1.channel(ch))
    hardware.NSC200(
        M = 'blah', P = 'blah', PORT = asyn.DeviceName(), CH = ch)

WriteIoc('iocs', 'TS', 'BLAH', 1)
