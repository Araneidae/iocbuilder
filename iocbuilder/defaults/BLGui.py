from iocbuilder import ModuleBase

try:
    from iocbuilder.modules.Hy8515 import _Hy8515channel

    class AsynHy8515channel(ModuleBase):

        ArgInfo = _Hy8515channel.ArgInfo + [
            ('asyn_name', str, 'Override Asyn name', None),
            ('input_eos', str, 'Input end of string (terminator)', None),
            ('output_eos', str, 'Output end of string (terminator)', None)
        ]
        XMLObjects = _Hy8515channel.XMLObjects

        def __init__(self,asyn_name,**args):
            # only available if he have asyn and Hy8515 before BLGui
            from iocbuilder.hardware import AsynSerial

            hkeys = [ x[0] for x in _Hy8515channel.ArgInfo ]
            hdict = dict( (k,args[k]) for k in args if k in hkeys)
            adict = dict( (k,args[k]) for k in args if k not in hkeys)
            self.channel = _Hy8515channel(**hdict)            
            self.asyn = AsynSerial(name=asyn_name,port=self.channel,**adict)

        def DeviceName(self):
            return self.asyn.DeviceName()
            
except ImportError:
    pass
