# Meta data argument info support.

import inspect

__all__ = ['makeArgInfo', 'addArgInfo']



class ArgInfo(object):
    '''This function produces an ArgInfo list for the xml frontend to 
    iocbuilder. It uses the arguments and defaults from the supplied init
    method and annotates them with types and descriptions. Example:

    class mybase(ModuleBase):
        def __init__(self, arg1, arg2=1):
            self.__super.__init__(self)
            ... do other stuff...

        ArgInfo = makeArgInfo(__init__,
            arg1 = (str, 'Description for arg1'),
            arg2 = (int, 'Description for arg2'))    
    

    Here ArgInfo contains the following fields:

        .descriptions       Dictionary mapping argument names to meta-data
        .required_names     List of mandatory arguments (without defaults)
        .default_names      List of arguments with default values
        .default_values     List of default values of arguments
        .optional_names     List of optional arguments.
    '''

    def __init__(self, __source=None, __optional=[], __method=True, **descs):
        self.descriptions = descs
        self.optional_names = __optional

        if callable(__source):
            # First get the names and defaults from the given function
            names, _, varkw, defaults = inspect.getargspec(__source)
            # If this is a bound method, discard the first argument.
            if __method:
                names = names[1:]
            if defaults:
                self.required_names = names[:-len(defaults)]
                self.default_names = names[-len(defaults):]
                self.default_values = defaults
            else:
                self.required_names = names
                self.default_names = []
                self.default_values = []

            if varkw:
                # Add any names in descs that we've not already accounted for
                # to the list of required names.  We sort the list so that
                # the ordering is at least predictable.
                self.required_names += sorted(list(
                    set(descs) - set(names) - set(__optional)))
            assert varkw or not __optional, \
                'Unusable optional arguments: %s' % __optional
        else:
            # Somewhat special case for taking the arguments from a list of
            # names.  These are treated as all mandatory.
            if __source:
                self.required_names = list(__source)
            else:
                self.required_names = []
            self.default_names = []
            self.default_values = []

        self.__validate()
        

    def __validate(self):
        # Validates the complete ArgInfo data.
        set_required = set(self.required_names)
        set_default  = set(self.default_names)
        set_optional = set(self.optional_names)

        # First check for duplicates in all the lists of names.
        assert len(set_optional) == len(self.optional_names), \
            'Duplicate optional names'
        assert len(set_required) == len(self.required_names), \
            'Duplicate required names'
        assert len(set_default) == len(self.default_names), \
            'Duplicate default names'
        # Check for overlaps between the lists
        assert \
            not (set_optional & set_required) and \
            not (set_required & set_default)  and \
            not (set_optional & set_default), 'Overlapping arguments?'

        # Check that all the names are described
        all_names = set_required | set_default | set_optional
        set_descs = set(self.descriptions)
        assert all_names <= set_descs, \
            'Arguments %s not described' % (all_names - set_descs)
        assert set_descs <= all_names, \
            'Descriptions for unknown arguments %s' % (set_descs - all_names)
            

        
    def Names(self, excludes=[]):
        '''Returns list of all possible argument names.  If excludes is given
        then it lists names that will not be returned.'''
        return [name
            for name in \
                self.required_names + self.default_names + self.optional_names
            if name not in excludes]

    def __add__(self, other):
        '''Aggregates information about two ArgInfo objects into a single
        object.  Any overlap of names is treated as an error.'''
        result = ArgInfo()
        result.descriptions = dict(self.descriptions, **other.descriptions)
        result.required_names = self.required_names + other.required_names
        result.default_names  = self.default_names  + other.default_names
        result.default_values = self.default_values + other.default_values
        result.optional_names = self.optional_names + other.optional_names
        self.__validate()
        return result
        

makeArgInfo = ArgInfo


def addArgInfo(__method=False, **descs):
    '''This is a decorator used to automatically add an ArgInfo attribute to
    a function.'''
    def decorator(f):
        f.ArgInfo = makeArgInfo(f, __method = __method, **descs)
        return f
    return decorator



# -----------------------------------------------------------------------------
#  Information about individual arguments.


__all__ += ['Simple', 'Choice', 'Enum', 'Ident', 'List', 'Sevr']

_simpleTypes = [int, str, float, bool]

class ArgType(object):
    _extras = ['values', 'labels', 'ident']
    def __init__(self, desc, typ, **extras):
        self.desc = str(desc)
        self.typ = typ
        for k in extras:
            assert k in self._extras, "%s is not one of %s" % (k, self._extras)
        self.__dict__.update(extras)        
            
def Simple(desc, typ):
    # just a simple type
    assert typ in _simpleTypes, \
        "%s is not a supported simple type %s" % (typ, _simpleTypes)    
    desc = "%s %s" % (desc, typ)
    return ArgType(desc, typ)
    
def Choice(desc, values, vlabels = None):
    # a choice of different values, with optional different labels
    typ = type(values[0])
    assert typ in _simpleTypes, \
        "%s is not a supported simple type %s" % (typ, _simpleTypes)     
    for v in values:
        assert typ == type(v), \
            "Value '%s' doesn't have same type as '%s'" % (v, values[0])
    desc = "%s %s\nValues:\n\t" % (desc, typ)
    if vlabels is None:
        descs = descs + "\n\t".join(map(str,values))
        return ArgType(typ, desc, labels = values)
    else:
        assert len(values) == len(vlabels), \
            "Value labels %s do not have the same length as values %s" % \
            (vlables, values)
        argdescs = [ "%s: %s" % x for x in zip(vlabels, values) ]        
        descs = descs + "\n\t".join(argdescs)
        return ArgType(typ, desc, values = values, labels = labels)

def Enum(desc, values):
    # a choice of different values, stores the index
    return Choice(desc, range(len(values)), values)

def Ident(desc, typ):
    # a choice of identifiers of a particular type
    assert issubclass(typ, ModuleBase), \
        "Identifier lookup only allowed on ModuleBase subclasses"
    descs = "%s %s" % (desc, typ)        
    return ArgType(typ, desc, ident = True)

def List(desc, num, func, *arg, **kwargs):
    # list of argtypes
    return [ func("%s %d"%(desc,i) *args, **kwargs) for i in range(num) ]

def Sevr(desc):
    # choice of possible values for SEVR field
    return Choice(desc, ["NO_ALARM","MINOR","MAJOR","INVALID"])


class test1(object):
    def __init__(self, a=1, b="string"):
        pass
    ArgInfo = makeArgInfo(__init__,
        a = Simple("Arg 1", int),
        b = Simple("Arg 2", str))

class test2(object):
    def __init__(self, c=12, d="string2"):
        pass
    ArgInfo = makeArgInfo(__init__,
        c = Simple("Arg 3", float),
        d = Simple("Arg 4", bool))
        
subclasses = [test1, test2]
