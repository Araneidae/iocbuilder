'''Support for generating epics records.'''

import string

import support
import recordnames
import recordset


__all__ = ['PP', 'CP', 'MS', 'NP', 'ImportRecord', 'ImportName']



# Converts a bound function to an unbound function which can then be rebound:
# the extra binding is passed as the first argument.
def _unbind(function):
    def wrapper(*args, **kargs):
        return function(*args, **kargs)
    return wrapper


#---------------------------------------------------------------------------
#
#   Record class

## Base class for all record types.
#
# All record types known to the IOC builder (loaded from DBD files in EPICS
# support modules) are subclasses of this class and are published as
# attributes of the \ref iocbuilder.dbd.records "records" class.
class Record(object):

    # Creates a subclass of the record with the given record type and
    # validator bound to the subclass.  The device used to load the record is
    # remembered so that it can subsequently be instantiated if necessary.
    @classmethod
    def CreateSubclass(cls, device, recordType, validate):
        # Each record we publish is a class so that individual record
        # classes can be subclassed when convenient.
        class BuildRecord(Record):
            _validate = validate
            _type = recordType
            _device = device
        BuildRecord.__name__ = recordType

        # Perform any class extension required for this particular record type.
        import bits
        return bits.ExtendClass(BuildRecord)


    ## Converts a short form record name into the full record name as it will
    # appear in the generated database.
    @classmethod
    def RecordName(cls, name):
        return recordnames.RecordNames.RecordName(name)


    __MetadataHooks = []

    # Called to add hooks for meta-data.  The hook class should provide
    # a function
    #     hook_cls.PrintMetadata(record)
    # which will be called as the record is generated.  All the given
    # hook_functions will be exported as methods of the class which will be
    # called with the class instance as its first argument.
    @classmethod
    def AddMetadataHook(cls, hook_cls, **hook_functions):
        cls.__MetadataHooks.append(hook_cls)
        for name, function in hook_functions.items():
            setattr(cls, name, _unbind(function))


    def __setattr(self, name, value):
        # Because we have hooked into __setattr__, we need to dance a little
        # to write names into our dictionary.
        if name[:2] == '__':
            self.__dict__['_Record' + name] = value
        else:
            self.__dict__[name] = value


    # Record constructor.  Needs to be told the type of record that this will
    # be, a field validation object (which will be used to check field names
    # and field value assignments), the name of the record being created, and
    # initialisations for any other fields.  Builds standard record name using
    # the currently configured RecordName hook.

    ## Record constructor.
    #
    # This is used to construct a record of a particular record type.  The
    # record is added to database of the generated IOC, or can simply be
    # written out to a separate .db file, depending on the chosen IOC writer.
    #
    # \param record
    #   The name of the record being generated.  The detailed name of the
    #   record is determined by the configured record name convention, and
    #   normally the device part of the record name is not specified here.
    # \param **fields
    #   All of the fields supported by the record type appear as attributes
    #   of the class.  Values can be specified in the constructor, or can be
    #   assigned subsequently to the generated instance.
    #
    # For example, the following code generates a record which counts how
    # many times it has been processed:
    #
    # \code
    #   cntr = records.calc('CNTR', CALC = 'A+1', VAL = 0)
    #   cntr.A = cntr
    # \endcode
    # This will generate a database somewhat like this:
    # \verbatim
    # record(calc, "$(DEVICE):CNTR")
    # {
    #     field(A,    "$(DEVICE):CNTR")
    #     field(CALC, "A+1")
    #     field(VAL,  "0")
    # }
    # \endverbatim
    #
    # Record links can be wrapped with PP(), CP(), MS() and NP() calls.
    def __init__(self, record, **fields):

        # Make sure the Device class providing this record is instantiated
        self._device._AutoInstantiate()

        # These assignment have to be directly into the dictionary to
        # bypass the tricksy use of __setattr__.
        self.__setattr('__fields', {})
        self.__setattr('name', self.RecordName(record))

        # Support the special 'address' field as an alias for either INP or
        # OUT, depending on which of those exists.  We only set up this field
        # if exactly one of INP or OUT is present as a valid field.
        address = [field
            for field in ['INP', 'OUT']
            if self.ValidFieldName(field)]
        if len(address) == 1:
            self.__setattr('address', address[0])
        else:
            self.__setattr('address', 'address')

        # Make sure all the fields are properly processed and validated.
        for name, value in fields.items():
            setattr(self, name, value)

        recordset.PublishRecord(self.name, self)



    # Call to generate database description of this record.  Outputs record
    # definition in .db file format.  Hooks for meta-data can go here.
    def Print(self):
        print
        for hook in self.__MetadataHooks:
            hook(self)
        print 'record(%s, "%s")' % (self._type, self.name)
        print '{'
        # Print the fields in alphabetical order.  This is more convenient
        # to the eye and has the useful side effect of bypassing a bug
        # where DTYPE needs to be specified before INP or OUT fields.
        keys = self.__fields.keys()
        keys.sort()
        for k in keys:
            value = self.__fields[k]
            if getattr(value, 'ValidateLater', False):
                self.__ValidateField(k, value)
            value = str(value)
            padding = ''.ljust(4-len(k))  # To align field values
            print '    field(%s, %s"%s")' % (k, padding, value)
        print '}'


    ## The string for a record is just its name.
    def __str__(self):
        return self.name

    # The representation string for a record identifies its type and name,
    # but we can't do much more.
    def __repr__(self):
        return '<record %s "%s">' % (self._type, self.name)

    # Calling the record generates a self link with a list of specifiers.
    def __call__(self, *specifiers):
        return _Link(self, None, *specifiers)


    ## Assigning to a record attribute updates a field.
    def __setattr__(self, fieldname, value):
        if fieldname == 'address':
            fieldname = self.__address
        if value is None:
            # Treat assigning None to a field the same as deleting that field.
            # This is convenient for default arguments.
            if fieldname in self.__fields:
                del self.__fields[fieldname]
        else:
            # If the field is callable we call it first: this is used to
            # ensure we convert record pointers into links.  It's unlikely
            # that this will have unfortunate side effects elsewhere, but it's
            # always possible...
            if callable(value):
                value = value()
            if not getattr(value, 'ValidateLater', False):
                self.__ValidateField(fieldname, value)
            self.__fields[fieldname] = value

    # Field validation
    def __ValidateField(self, fieldname, value):
        # If the field can validate itself then ask it to, otherwise use our
        # own validation routine.  This is really just a hook for parameters
        # so that they can do their own validation.
        if hasattr(value, 'Validate'):
            value.Validate(self, fieldname)
        else:
            self._validate.ValidFieldValue(fieldname, str(value))

    # Allow individual fields to be deleted from the record.
    def __delattr__(self, fieldname):
        if fieldname == 'address':
            fieldname = self.__address
        del self.__fields[fieldname]


    ## Reading a record attribute returns a link to the field.
    def __getattr__(self, fieldname):
        if fieldname == 'address':
            fieldname = self.__address
        self._validate.ValidFieldName(fieldname)
        return _Link(self, fieldname)

    ## Can be called to validate the given field name, returns True iff this
    # record type supports the given field name.
    @classmethod
    def ValidFieldName(cls, fieldname):
        try:
            # The validator is specified to raise an AttributeError exception
            # if the field name cannot be validated.  We translate this into
            # a boolean here.
            cls._validate.ValidFieldName(fieldname)
        except AttributeError:
            return False
        else:
            return True

    @classmethod
    def FieldInfo(cls):
        return cls._validate.FieldInfo()

    # When a record is pickled for export it will reappear as an ImportRecord
    # instance.  This makes more sense (as the record has been fully generated
    # already), and avoids a lot of trouble.
    def __reduce__(self):
        return (ImportRecord, (self.name, self._type))



## Records can be imported by name.  An imported record has no specification
# of its type, and so no validation can be done: all that can be done to an
# imported record is to link to it.
class ImportRecord:
    def __init__(self, name, type=None):
        self.name = name
        self.__type = type
        if type:
            # Need to find the dbd and ask it for a validator
            self.__validate = None
        else:
            self.__validate = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<external record %s "%s">' % (self.__type, self.name)

    def __call__(self, *specifiers):
        return _Link(self, None, *specifiers)

    def __getattr__(self, fieldname):
        if self.__validate:
            self.__validate.ValidFieldName(fieldname)
        else:
            # Brain-dead minimal validation: just check for all uppercase!
            ValidChars = set(string.ascii_uppercase + string.digits)
            if not set(fieldname) <= ValidChars:
                raise AttributeError, 'Invalid field name %s' % fieldname
        return _Link(self, fieldname)


def ImportName(name):
    '''Creates import of record with currently configured device name.'''
    return ImportRecord(recordnames.RecordName(name))


# A link is a class to encapsulate a process variable link.  It remembers
# the record, the linked field, and a list of specifiers (such as PP, CP,
# etcetera).
class _Link:
    def __init__(self, record, field, *specifiers):
        self.record = record
        self.field = field
        self.specifiers = specifiers

    def __str__(self):
        result = self.record.name
        if self.field:
            result += '.' + self.field
        for specifier in  self.specifiers:
            result += ' ' + specifier
        return result

    def __call__(self, *specifiers):
        return _Link(self.record, self.field, *self.specifiers + specifiers)

    # Returns the value currently assigned to this field.
    def Value(self):
        return self.record._Record__fields[self.field]



# Some helper routines for building links

## "Process Passive": any record update through a PP output link will be
# processed if its scan is Passive.
def PP(record):
    return record('PP')

## "Channel Process": a CP input link will cause the linking record to process
# any time the linked record is updated.
def CP(record):
    return record('CP')

## "Maximise Severity": any alarm state on the linked record is propogated to
# the linking record.
def MS(record):
    return record('MS')

## "No Process": the linked record is not processed.
def NP(record):
    return record('NPP')

# ... put the rest in some time
