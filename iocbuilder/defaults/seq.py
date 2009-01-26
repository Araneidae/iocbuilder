from iocbuilder import Device
from iocbuilder.support import quote_c_string

__all__ = ['Seq', 'Sequencer']


class Seq(Device):
    # The order here matters!  seq depends on symbols in pv, so pv needs to
    # appear first.
    LibFileList = ['pv', 'seq']
    AutoInstantiate = True


class Sequencer(Device):
    Dependencies = (Seq,)
    BaseClass = True

    # The following need to be overridden
    Arguments = ()
    ProgramName = None

    __BuiltinParameters = set(['logfile', 'name', 'stack', 'priority'])

    def __init__(self, **args):
        self.__super.__init__()
        
        assert set(set(args.keys()) - self.__BuiltinParameters) == \
                set(self.Arguments), \
            'Arguments missing or not recognised'
        assert self.ProgramName is not None, \
            'Need to ensure class has a sequence name specified'
        
        self.args = args

    def PostIocInitialise(self):
        if self.args:
            args = ', %s' % quote_c_string(', '.join([
                "%s=%s" % (param, value)
                for param, value in self.args.items()]))
        else:
            args = ''
        print 'seq &%s%s' % (self.ProgramName, args)
