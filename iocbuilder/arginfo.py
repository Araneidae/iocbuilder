'''Meta data argument info support.'''

import inspect, sys
from libversion import ModuleBase

__all__ = ['makeArgInfo', 'filter_dict']

## Returns dictionary \c d with keys restricted to entries in the list \c l
# \param d Dictionary to filter
# \param l List to filter dictionary keys by
def filter_dict(d, l):
    return dict((n, d[n]) for n in set(l) & set(d))


## This function produces an ArgInfo list for the xml frontend to
# iocbuilder. It uses the arguments and defaults from the supplied init
# method and annotates them with types and descriptions. Example:
#
# \code
# class mybase(ModuleBase):
#     def __init__(self, arg1, arg2=1):
#         self.__super.__init__(self)
#         ... do other stuff...
#
#     ArgInfo = makeArgInfo(__init__,
#         arg1 = Simple('Description for arg1', str),
#         arg2 = Simple('Description for arg2', int))
# \endcode
class ArgInfo(object):
    # Here ArgInfo contains the following fields:
    #
    #     .descriptions       Dictionary mapping argument names to meta-data
    #     .required_names     List of mandatory arguments (without defaults)
    #     .default_names      List of arguments with default values
    #     .default_values     List of default values of arguments
    #     .optional_names     List of optional arguments.

    def __init__(self, __source=None, __optional=[], __method=True, **descs):
        self.descriptions = descs
        for k, v in descs.items():
            assert isinstance(v, ArgType), \
                'ArgInfo description "%s" is not of valid type. Got:\n%s' % \
                    (k, v)
        self.optional_names = list(__optional)

        if callable(__source):
            # First get the names and defaults from the given function
            names, _, varkw, defaults = inspect.getargspec(__source)
            # If this is a bound method, discard the first argument.
            if __method:
                names = names[1:]
            if defaults:
                self.required_names = names[:-len(defaults)]
                self.default_names = names[-len(defaults):]
                self.default_values = list(defaults)
            else:
                self.required_names = names
                self.default_names = []
                self.default_values = []

            if varkw:
                # Add any names in descs that we've not already accounted for
                # to the list of optional names.  We sort the list so that
                # the ordering is at least predictable.
                self.required_names += sorted(list(
                    set(descs) - set(names) - set(__optional)))
            assert varkw or not __optional, \
                'Unusable optional arguments: %s' % self.optional_names
        else:
            # Somewhat special case for taking the arguments from a list of
            # names.  These are treated as all mandatory.
            if __source:
                self.required_names = list(__source)
            else:
                self.required_names = sorted(set(descs) - set(__optional))
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

    ## Returns list of all possible argument names.  If excludes is given
    # then it lists names that will not be returned.
    def Names(self, without=[]):
        return [name
            for name in \
                self.required_names + self.default_names + self.optional_names
            if name not in without]

    ## Aggregates information about two ArgInfo objects into a single
    # object.  Argument details in the second ArgInfo object override settings
    # in the first.
    def __add__(self, other):
        result = ArgInfo()
        result.descriptions = dict(self.descriptions, **other.descriptions)
        result.required_names = self.required_names[:]
        result.default_names  = self.default_names[:]
        result.default_values = self.default_values[:]
        result.optional_names = self.optional_names[:]

        # Because any type of argument can be convered to any other type, but
        # we are keen to preserve argument order, the process of merging is
        # rather involved.
        def del_required(name):
            if name in result.required_names:
                result.required_names.remove(name)
        def del_optional(name):
            if name in result.optional_names:
                result.optional_names.remove(name)
        def del_default(name):
            if name in result.default_names:
                i = result.default_names.index(name)
                del result.default_names[i]
                del result.default_values[i]

        for name in other.required_names:
            del_optional(name)
            del_default(name)
            if name not in result.required_names:
                result.required_names.append(name)
        for (name, value) in zip(other.default_names, other.default_values):
            del_required(name)
            del_optional(name)
            if name in result.default_names:
                result.default_values[result.default_names.index(name)] = value
            else:
                result.default_names.append(name)
                result.default_values.append(value)
        for name in other.optional_names:
            del_required(name)
            del_default(name)
            if name not in result.optional_names:
                result.optional_names.append(name)

        result.__validate()
        return result

    ## Return a new ArgInfo object. If including is specified, then only
    # include the argument descriptions for each arg in including. If without
    # is specified, then don't include argument descriptions for each arg in
    # without.
    def filtered(self, including = None, without = None):
        assert including is None or without is None, \
            'Can\'t filter and filter-out argInfo in the same operation'
        result = ArgInfo()
        result.descriptions = dict()
        names = self.Names()
        if without is not None:
            names = [name for name in names if name not in without]
        elif including is not None:
            names = [name for name in names if name in including]
        for name in names:
            if name in self.required_names:
                result.required_names.append(name)
            elif name in self.default_names:
                result.default_names.append(name)
                result.default_values.append(
                    self.default_values[self.default_names.index(name)])
            elif name in self.optional_names:
                result.optional_names.append(name)
            result.descriptions[name] = self.descriptions[name]
        result.__validate()
        return result

makeArgInfo = ArgInfo



# -----------------------------------------------------------------------------
#  Information about individual arguments.


__all__ += ['Simple', 'Choice', 'Enum', 'Ident', 'Sevr']

## These are the types supported by the Simple function
_simpleTypes = [int, str, float, bool]

## This is the base class that Simple, Choice, etc. create instanced of. It
#  is not meant to be instantiated directly'''
class ArgType(object):
    _extras = ['values', 'labels', 'ident']
    def __init__(self, desc, typ, **extras):
        self.desc = str(desc)
        self.typ = typ
        for k in extras:
            assert k in self._extras, '%s is not one of %s' % (k, self._extras)
        self.__dict__.update(extras)

## Just a simple type.
# \param desc Description of the argument
# \param typ Type of the argument, one of _simpleTypes
def Simple(desc, typ=str):
    assert typ in _simpleTypes, \
        '%s is not a supported simple type %s' % (typ, _simpleTypes)
    if typ == bool:
        return Choice(desc, [False, True], ['False', 'True'])
    else:
        desc = '%s\n%s' % (desc, typ)
        return ArgType(desc, typ)

## A choice of different values, with optional different labels
# \param desc Description of the argument
# \param values List of possible values, type must be one of _simpleTypes, and
# the same for all in the list of values
# \param labels List of optional labels for the values
def Choice(desc, values, labels = None):
    typ = type(values[0])
    assert typ in _simpleTypes, \
        '%s is not a supported simple type %s' % (typ, _simpleTypes)
    for v in values:
        assert typ == type(v), \
            'Value "%s" doesn\'t have same type as "%s"' % (v, values[0])
    desc = '%s\n%s\nValues:\n ' % (desc, typ)
    if labels is None:
        desc += '\n '.join(map(str, values))
        return ArgType(desc, typ, labels = values)
    else:
        assert len(values) == len(labels), \
            'Labels %s do not have the same length as values %s' % \
            (labels, values)
        argdescs = [ '%s: %s' % x for x in zip(labels, values) ]
        desc += '\n '.join(argdescs)
        return ArgType(desc, typ, values = values, labels = labels)

## Like Choice, but stores the index instead of the value
# \param desc Description of the argument
# \param values List of possible values, type must be one of _simpleTypes, and
# the same for all in the list of values
def Enum(desc, values):
    return Choice(desc, range(len(values)), values)

## A choice of identifiers of a particular type
# \param desc Description of the argument
# \param typ Class of the argument, argument must be a subclass of this class.
# xmlbuilder will look at all the defined objects so far, and offer a selection
# of those that are a subclass of \c typ as options for this argument
def Ident(desc, typ):
    desc = '%s\n%s' % (desc, typ)
    return ArgType(desc, typ, ident = True)

## choice of possible values for SEVR field
# \param desc Description of the argument
def Sevr(desc):
    return Choice(desc, ['NO_ALARM', 'MINOR', 'MAJOR', 'INVALID'])
