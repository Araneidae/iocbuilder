# Implements the set of records provided by a dbd

import os, os.path
import ctypes

import mydbstatic   # Pick up interface to EPICS dbd files
from support import Singleton

from recordbase import Record


__all__ = ['records']


# This class contains all the record types current supported by the loaded
# dbd, and is published to the world as epics.records.  As records are added
# (in response to calls to LoadDbdFile) they are automatically available to
# all targets.
class RecordTypes(Singleton):
    def __init__(self):
        self.__RecordTypes = set()

    def PublishRecordType(self, recordType, validate):
        # Each record we publish is a class so that individual record
        # classes can be subclassed when convenient.
        class BuildRecord(Record):
            def __init__(self, record, **fields):
                Record.__init__(
                    self, recordType, validate, record, **fields)
        BuildRecord.__name__ = recordType

        # Perform any class extension required for this particular record type.
        import bits
        BuildRecord = bits.ExtendClass(BuildRecord)
        # Publish this record type and remember it
        self.__RecordTypes.add(recordType)
        setattr(self, recordType, BuildRecord)

    def __contains__(self, recordType):
        '''Checks whether the given recordType names a known valid record
        type.'''
        return recordType in self.__RecordTypes


# This class will be published to the outside world as "records", the
# collection of available record types.
records = RecordTypes


# Note: the _DBD class is really just a wrapper for LoadDbdFile, so there is
# no point in creating this singleton class!

class _DBD(Singleton):
    def __init__(self):
        self.__db = ctypes.c_void_p()

    def __del__(self):
        assert False, 'Do we even get to here?!'
        # We test for the existence of mydbstatic because of a curious lifetime
        # issue during shutdown: it's entirely possible that the mydbstatic
        # module gets unloaded *before* this method gets called!
        #    Even worse, it seems we can be called while mydbstatic is being
        # unloade and dbFreeBase is None!
        if self.__db and mydbstatic and mydbstatic.dbFreeBase:
            mydbstatic.dbFreeBase(self.__db)

    def LoadDbdFile(self, dbdDir, dbdfile):
        # Read the specified dbd file into the current database.  This allows
        # us to see any new definitions.
        from hardware import baselib
        curdir = os.getcwd()
        os.chdir(dbdDir)
        status = mydbstatic.dbReadDatabase(
            ctypes.byref(self.__db), dbdfile,
            '.:%s/dbd' % baselib.EpicsBasePath(), None)
        assert status == 0, 'Error reading database %s/%s (status %d)' % \
            (dbdDir, dbdfile, status)
        os.chdir(curdir)

        # Now export any new names made available
        self.__BuildRecordClasses()


    # This method builds all the epics records
    def __BuildRecordClasses(self):
        # Enumerate all the record types and build a record generator class
        # for each one that we've not seen before.
        entry = mydbstatic.dbAllocEntry(self.__db)
        status = mydbstatic.dbFirstRecordType(entry)
        while status == 0:
            recordType = mydbstatic.dbGetRecordTypeName(entry)
            if not hasattr(RecordTypes, recordType):
                self.__BuildRecordClass(entry, recordType)
            status = mydbstatic.dbNextRecordType(entry)
        mydbstatic.dbFreeEntry(entry)


    # Builds an instance of a generic record building class
    def __BuildRecordClass(self, entry, recordType):
        validate = ValidateDbField(self, entry)
        RecordTypes.PublishRecordType(recordType, validate)

        

# This class uses a the static database to validate whether the associated
# record type allows a given value to be written to a given field.
class ValidateDbField:
    def __init__(self, dbd, dbEntry):
        # Hang on to the calling dbd to ensure that the parent database
        # doesn't go away prematurely.
        self.dbd = dbd
        self.dbEntry = mydbstatic.dbCopyEntry(dbEntry)

    def __del__(self):
        if mydbstatic:
            mydbstatic.dbFreeEntry(self.dbEntry)

    # This method raises an attribute error if the given field name is
    # invalid.  As an important side effect it also sets the database
    # cursor to the appropriate database descriptor.
    def ValidFieldName(self, name):
        # Search for the named field in the database
        status = mydbstatic.dbFirstField(self.dbEntry, 0)
        while status == 0:
            if mydbstatic.dbGetFieldName(self.dbEntry) == name:
                # Good, found it
                break
            status = mydbstatic.dbNextField(self.dbEntry, 0)
        else:
            # Hmm.  Got to end of loop without finding the name.  No good
            raise AttributeError, 'Invalid field name %s' % name

    # This method raises an exeption if the given field name does not exist
    # or if the value cannot be validly written.
    def ValidFieldValue(self, name, value):
        # First check the field name is valid and set the cursor in focus.
        self.ValidFieldName(name)
        value = str(value)

        # Now see if we can write the value to it
        message = mydbstatic.dbVerify(self.dbEntry, value)
        assert message == None, \
            'Can\'t write "%s" to field %s: %s' % (value, name, message)


LoadDbdFile = _DBD.LoadDbdFile
