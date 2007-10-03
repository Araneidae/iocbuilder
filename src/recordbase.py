# Support for generating epics records.

import string

import support, recordset


__all__ = ['PP', 'CP', 'MS', 'NP', 'ImportRecord', 'Parameter']



def BindNames(recordnames):
    Record.BindNames(recordnames)



#---------------------------------------------------------------------------
#
#   Record class    

class Record(object):
    '''Base class for all record types.'''

    # Configuration hook used for record names.  This is defined during
    # startup configuration and may change during normal operation.
    __recordnames = None
    
    @classmethod
    def BindNames(cls, recordnames):
        '''Binds the records to their naming convention.'''
        cls.__recordnames = recordnames
        
    @classmethod
    def RecordName(cls, name):
        '''Converts a short form record name into the full record name as it
        will appear in the generated database.'''
        return cls.__recordnames.RecordName(name)


    # Builds standard record name using the currently configured RecordName
    # hook.
    def __init__(self, type, validate, record, **fields):
        '''Record constructor.  Needs to be told the type of record that
        this will be, a field validation object (which will be used to
        check field names and field value assignments), the name of the
        record being created, and initialisations for any other fields.'''
        
        # These assignment have to be directly into the dictionary to
        # bypass the tricksy use of __setattr__.
        self.__dict__['_Record__type'] = type
        self.__dict__['_Record__validate'] = validate
        self.__dict__['_Record__fields'] = {}
        self.__dict__['_Record__autosaves'] = set()
        self.__dict__['name'] = self.RecordName(record)

        # Support the special 'address' field as an alias for either INP or
        # OUT, depending on which of those exists.  We only set up this field
        # if exactly one of INP or OUT is present as a valid field. 
        address = [field
            for field in ['INP', 'OUT']
            if self.ValidFieldName(field)]
        if len(address) == 1:
            self.__dict__['_Record__address'] = address[0]
        else:
            self.__dict__['_Record__address'] = 'address'
        
        # Make sure all the fields are properly processed and validated.
        for name, value in fields.items():
            setattr(self, name, value)

        recordset.PublishRecord(self.name, self)


    def Autosave(self, *fieldnames):
        '''Enables named field(s) for autosave and restore.'''
        for fieldname in fieldnames:
            self.__validate.ValidFieldName(fieldname)
            self.__autosaves.add(fieldname)



    # Call to generate database description of this record.
    def Print(self):
        '''Outputs record definition in .db file format.  Hooks for
        meta-data can go here.'''
        print
        for field in self.__autosaves:
            print '#%% autosave 0 %s' % field
        print 'record(%s, "%s")' % (self.__type, self.name)
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


    def PrintAutosaves(self):
        for fieldname in self.__autosaves:
            print '%s.%s' % (self.name, fieldname)

    def CountAutosaves(self):
        return len(self.__autosaves)
            

    # The string for a record is just its name.
    def __str__(self):
        return self.name

    # The representation string for a record identifies its type and name,
    # but we can't do much more.
    def __repr__(self):
        return '<record %s "%s">' % (self.__type, self.name)

    # Calling the record generates a self link with a list of specifiers.
    def __call__(self, *specifiers):
        return _Link(self, None, *specifiers)
        

    # Assigning to a record attribute updates a field.
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
            self.__validate.ValidFieldValue(fieldname, str(value))

    # Allow individual fields to be deleted from the record.
    def __delattr__(self, fieldname):
        if fieldname == 'address':
            fieldname = self.__address
        del self.__fields[fieldname]


    # Reading a record attribute returns a link to the record.
    def __getattr__(self, fieldname):
        if fieldname == 'address':
            fieldname = self.__address
        self.__validate.ValidFieldName(fieldname)
        return _Link(self, fieldname)

    def ValidFieldName(self, fieldname):
        '''Can be called to validate the given field name, returns True iff
        this record type supports the given field name.'''
        try:
            # The validator is specified to raise an AttributeError exception
            # if the field name cannot be validated.  We translate this into
            # a boolean here.
            self.__validate.ValidFieldName(fieldname)
        except AttributeError:
            return False
        else:
            return True

    # When a record is pickled for export it will reappear as an ImportRecord
    # instance.  This makes more sense (as the record has been fully generated
    # already), and avoids a lot of trouble.
    def __reduce__(self):
        return (ImportRecord, (self.name, self.__type))



# Class to wrap an imported record name.  This should behave much the same
# as a real record, but of course we can't add fields and we may even not
# know the type of the record.  So in practice all we can really do is to
# create links.
#
# It may be possible to unify this class with the Record class.
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

    def Value(self):
        '''Returns the value currently assigned to this field.'''
        return self.record._Record__fields[self.field]

    def autosave(self):
        self.record.Autosave(self.field)

    def burt(self):
        self.record.Burt(self.field)


class Parameter:
    '''A Parameter is used to wrap a template parameter before being assigned
    to a record field.'''
    
    def __init__(self, name):
        self.__name = name

    def __str__(self):
        return '$(%s)' % self.__name

    def Validate(self, record, field):
        '''Parameter validation always succeeds!'''
        return True


# Some helper routines for building links

# PP: Process Passive.  Any record updated through a PP link is processed if
# it is set for passive scan.
def PP(record):
    '''"Process Passive": any record update through a PP output link will be
    processed if its scan is Passive.'''
    return record('PP')


def CP(record):
    '''"Channel Process": a CP input link will cause the linking record to
    process any time the linked record is updated.'''
    return record('CP')

def MS(record):
    '''"Maximise Severity": any alarm state on the linked record is propogated
    to the linking record.'''
    return record('MS')

def NP(record):
    '''"No Process": the linked record is not processed.'''
    return record('NPP')

# ... put the rest in some time
