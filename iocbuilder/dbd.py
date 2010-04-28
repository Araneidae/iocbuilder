'''Implements the set of records provided by a dbd'''

import os, os.path
import ctypes

import mydbstatic   # Pick up interface to EPICS dbd files
import paths
import arginfo
from support import Singleton, OrderedDict

from recordbase import Record


__all__ = ['records']


# This class contains all the record types current supported by the loaded
# dbd, and is published to the world as epics.records.  As records are added
# (in response to calls to LoadDbdFile) they are automatically available to
# all targets.
class RecordTypes(Singleton):
    def __init__(self):
        self.__RecordTypes = set()

    def GetRecords(self):
        return sorted(self.__RecordTypes)

    def _PublishRecordType(self, device, recordType, validate):
        # Publish this record type and remember it
        # \todo If we remember which dbd the record came from we can be
        # intelligent about loading it again
        self.__RecordTypes.add(recordType)
        setattr(self, recordType,
            Record.CreateSubclass(device, recordType, validate))

    # Checks whether the given recordType names a known valid record type.
    def __contains__(self, recordType):
        return recordType in self.__RecordTypes


## Every record type loaded from a DBD is present as an attribute of this
## class with the name of the record type.
#
# For example, to create an ai record, simply write
# \code
#   records.ai('NAME', DESC = 'A test ai record', EGU = 'V')
# \endcode
#
# Each record is of type \ref iocbuilder.recordbase.Record "Record", see for
# more details.
records = RecordTypes

# Possible field types as returned by dbGetFieldType
DCT_STRING = 0
DCT_INTEGER = 1
DCT_REAL = 2
DCT_MENU = 3
DCT_MENUFORM = 4
DCT_INLINK = 5
DCT_OUTLINK = 6
DCT_FWDLINK = 7
DCT_NOACCESS = 8

# This class uses a the static database to validate whether the associated
# record type allows a given value to be written to a given field.
class ValidateDbField:
    def __init__(self, dbEntry):
        self.dbEntry = mydbstatic.dbCopyEntry(dbEntry)
        self._FieldInfo = None
        self._ValidNamesSet = None

    # Computes list of valid names and creates associated arginfo
    # definitions.  This is postponed quite late to try and ensure the menus
    # are fully populated, in other words we don't want to fire this until
    # all the dbd files have been loaded.
    def __ProcessDbd(self):
        # ordered dict of field_name -> arginfo
        self._FieldInfo = OrderedDict()
        valid_names = []
        status = mydbstatic.dbFirstField(self.dbEntry, 0)
        while status == 0:
            name = mydbstatic.dbGetFieldName(self.dbEntry)
            desc = mydbstatic.dbGetPrompt(self.dbEntry)
            typ = mydbstatic.dbGetFieldType(self.dbEntry)
            group = mydbstatic.dbGetPromptGroup(self.dbEntry)
            if typ in [DCT_STRING, DCT_INLINK, DCT_OUTLINK, DCT_FWDLINK]:
                ArgInfo = arginfo.Simple(desc, str)
            elif typ in [DCT_INTEGER]:
                ArgInfo = arginfo.Simple(desc, int)
            elif typ in [DCT_REAL]:
                ArgInfo = arginfo.Simple(desc, float)
            elif typ in [DCT_MENU, DCT_MENUFORM]:
                n_choices = mydbstatic.dbGetNMenuChoices(self.dbEntry)
                if n_choices > 0:
                    menu_void = mydbstatic.dbGetMenuChoices(self.dbEntry)
                    menu_p = ctypes.cast(menu_void,
                        ctypes.POINTER(ctypes.c_char_p * n_choices))
                    ArgInfo = arginfo.Choice(desc, list(menu_p[0]))
                else:
                    ArgInfo = arginfo.Simple(desc, str)
            else:
                # No access field.
                ArgInfo = None
            if name != "NAME":
                valid_names.append(name)
                if ArgInfo is not None:
                    self._FieldInfo[name] = ArgInfo
            status = mydbstatic.dbNextField(self.dbEntry, 0)

        self._ValidNamesSet = set(valid_names)

    def FieldInfo(self):
        if self._FieldInfo is None:
            self.__ProcessDbd()
        return self._FieldInfo

    def ValidNamesSet(self):
        if self._ValidNamesSet is None:
            self.__ProcessDbd()
        return self._ValidNamesSet

    # This method raises an attribute error if the given field name is
    # invalid.  As an important side effect it also sets the database
    # cursor to the appropriate database descriptor.
    def ValidFieldName(self, name):
        if name not in self.ValidNamesSet():
            raise AttributeError, 'Invalid field name %s' % name

    # This method raises an exeption if the given field name does not exist
    # or if the value cannot be validly written.
    def ValidFieldValue(self, name, value):
        # First check the field name is valid and set the cursor in focus.
        self.ValidFieldName(name)
        value = str(value)

        # Set the database cursor to the field
        status = mydbstatic.dbFirstField(self.dbEntry, 0)
        while status == 0:
            if mydbstatic.dbGetFieldName(self.dbEntry) == name:
                break
            status = mydbstatic.dbNextField(self.dbEntry, 0)

        # Now see if we can write the value to it
        message = mydbstatic.dbVerify(self.dbEntry, value)
        assert message == None, \
            'Can\'t write "%s" to field %s: %s' % (value, name, message)



# The same database pointer is used for all DBD files: this means that all
# the DBD entries are accumulated into a single large database.
_db = ctypes.c_void_p()

def LoadDbdFile(device, dbdDir, dbdfile):
    # Read the specified dbd file into the current database.  This allows
    # us to see any new definitions.  The device used to load the record is
    # also recorded for later use.
    curdir = os.getcwd()
    os.chdir(dbdDir)

    status = mydbstatic.dbReadDatabase(
        ctypes.byref(_db), dbdfile, '.:%s/dbd' % paths.EPICS_BASE, None)
    assert status == 0, 'Error reading database %s/%s (status %d)' % \
        (dbdDir, dbdfile, status)

    os.chdir(curdir)


    # Enumerate all the record types and build a record generator class
    # for each one that we've not seen before.
    entry = mydbstatic.dbAllocEntry(_db)
    status = mydbstatic.dbFirstRecordType(entry)
    while status == 0:
        recordType = mydbstatic.dbGetRecordTypeName(entry)
        if not hasattr(RecordTypes, recordType):
            validate = ValidateDbField(entry)
            RecordTypes._PublishRecordType(device, recordType, validate)
        status = mydbstatic.dbNextRecordType(entry)
    mydbstatic.dbFreeEntry(entry)
