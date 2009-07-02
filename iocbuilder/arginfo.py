# Meta data argument info support.

import inspect

__all__ = ['makeArgInfo', 'addArgInfo']



class ArgInfo(object):
    '''This function produces an ArgInfo list for the xml frontend to 
    iocbuilder. It uses the arguments and defaults from the supplied init
    method and annotates them with types and descriptions. Example:

    class mybase(ModuleBase):
        def __init__(self, arg1, arg2=1):
            # make arg appear as self.arg for all __init__ arguments
            self.__dict__.update(locals())
            ModuleBase.__init__(self)

        ArgInfo = makeArgInfo(__init__,
            arg1 = (str, 'Description for arg1'),
            arg2 = (int, 'Description for arg2')
        )    
    
    ArgInfo has the format:
    
    ArgInfo = [
        ('arg1', str, 'Description for arg1'),
        ('arg2', int, 'Description for arg2', 1)
    ]

    '''

    def __init__(self, __source=None, __optional=[], __method=True, **descs):
        '''
        '''

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
        else:
            if __source:
                self.required_names = list(__source)
            else:
                self.required_names = []
            self.default_names = []
            self.default_values = []
            varkw = False


        # Some set arithmetic to facilitate checking and calculations
        set_names = set(self.required_names) | set(self.default_names)
        set_optional = set(__optional)
        set_descs = set(descs)
        missing = (set_names | set_optional) - set_descs
        extra_names = set_descs - set_names - set_optional
        duplicates = set_names & set_optional

        # Any extra names are added to the list of required names
        self.required_names += sorted(list(extra_names))
        
        # Validate the arguments.
        assert not duplicates, \
            'Duplication of arguments: %s' % list(duplicates)
        assert not missing, 'No description for arguments: %s' % list(missing)
        assert varkw or not extra_names, \
            'Unexpected optional arguments: %s' % list(extra_names)
        assert varkw or not __optional, \
            'Unusable optional arguments: %s' % __optional

    def __validate(self):
        assert len(set(self.optional_names)) == len(self.optional_names), \
            'Duplicate optional names'
        assert len(set(self.required_names)) == len(self.required_names), \
            'Duplicate required names'
        assert len(set(self.default_names)) == len(self.default_names), \
            'Duplicate default names'

        
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
        result.optional_names = self.optional_names + other.optional_names
        result.required_names = self.required_names + other.required_names
        result.default_names  = self.default_names  + other.default_names
        result.default_values = self.default_values + other.default_values
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


_simpleTypes = [int, str, float, bool]

class ArgType(object):
    def __init__(self, desc, typ, validator=None, **extras):
        self.desc = desc
        self.typ = typ
        self.validator = validator
        self.__dict__.update(extras)
        
            
def Simple(desc, typ, validator = None):
    # just a simple type
    assert typ in _simpleTypes, \
        "%s is not a supported simple type %s" % (typ, _simpleTypes)    
    desc = "%s %s" % (desc, typ)
    return ArgType(typ, desc, validator)
    
def Choice(desc, values, vlabels = None):
    # a choice of different values, with optional different labels
    typ = type(values[0])
    assert typ in _simpleTypes, \
        "%s is not a supported simple type %s" % (typ, _simpleTypes)     
    for v in values:
        assert typ == type(v), \
            "Value '%s' doesn't have same type as '%s'" % (v, values[0])
    desc = "%s %s" % (desc, typ)
    if vlabels is None:
        vlabels = values    
        argdescs = values
    else:
        assert len(values) == len(vlabels), \
            "Value labels %s do not have the same length as values %s" % \
            (vlables, values)
        argdescs = [ "%s: %s" % x for x in zip(vlabels, values) ]        
    descs = "%s\nValues:\n\t" % descs + "\n\t".join(argdescs)
    return ArgType(typ, desc, args = zip(vlabels,values))

def Enum(desc, values):
    # a choice of different values, stores the index
    return Choice(desc, values, range(len(values)))

def Ident(desc, typ):
    # a choice of identifiers of a particular type
    assert issubclass(typ, ModuleBase), \
        "Identifier lookup only allowed on ModuleBase subclasses"
    descs = "%s %s" % (desc, typ)        
    return ArgType(typ, desc)

def Range(desc, *vals):
    assert len(vals) in (1, 2), \
        "Usage: Range(desc, min, max) or Range(desc, max)"
    typ = type(vals[0])
    assert typ in _simpleTypes, "%s is not a supported simple type %s" % \
        (typ, _simpleTypes)
    ran = range(*vals)
    if len(ran) < 11:
        # we can probably display this as a Choice
        return Choice(desc, ran)
    else:
        txt = "range [%s..%s]"%(ran[0],ran[-1])
        def validator(x):
            if x in ran:
                return True
            else:
                return "X not in "+txt
        return ArgType(typ, "%s <%s>"%(desc, txt), validator)                
                                                    
class List(object):
    # a list of argtypes
    def __init__(self, desc, num, func, *arg, **kwargs):
        self.argtypes = [ func("%s %d"%(desc,i) *args, **kwargs) \
                            for i in range(num) ]

    def setDefault(self, val):
        # set this argument to be a default value for those specified in val
        for i,v in enumerate(val):
            self.argtypes[i].setDefault(v)
        # for the other ones set them to be the default typ
        for i in range(i,len(self.argtypes)):
            self.argtypes[i].setDefault(self.argtypes[i].typ())
               
    def setOptional(self):
        # set this argument to be an optional value
        for o in self.argtypes:  
            o.setOptional()

    def setParent(self, parent):
        # set the parent to call getArgs on    
        for o in self.argtypes:     
            o.setParent(parent) 
                                                                
    def applyQVariant(self, variant):
        # this avoids a dependency on Qt, applied by gui
        for o in self.argtypes:     
            o.applyQVariant(variant) 

    # at this point the classes will get split off in the gui, so no need to
    # implement anything else

def ipAddr(val):
    # validator for an ip address
    errStr = "Should be of format x[xx].x[xx].x[xx].x[xx][:x[x..]]"
    split = value.strip().split(":")
    if len(split) not in [1,2]:
        return errStr
    if len(split) == 2:
        if not split[1].isdigit():
            return errStr
    split = split[0].split(".")
    if len(split) == 4:
        return errStr
    for i in split:
        if not i.isdigit():
            return errStr
        if int(i) < 1 or int(i) > 255:
            return errStr
    return True

def checklen(l):
    # validator generator for length
    def validator(val):
        if len(val) <= l:
            return True
        else:
            return "Must be less than %d characters" % l

def Sevr(desc):
    return Choice(["NO_ALARM","MINOR","MAJOR","INVALID"], desc)
