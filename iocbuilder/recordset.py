# IOC initialisation support code

import os.path
import subprocess

import recordnames
from libversion import ModuleBase
from support import Singleton


__all__ = ['LookupRecord', 'Substitution']




class RecordSet(Singleton):
    def __init__(self):
        self.Reset()

    def Reset(self):
        self.__RecordSet = {}

    def PublishRecord(self, name, record):
        '''Add a record to the list of records to be published.'''
        assert name not in self.__RecordSet, 'Record %s already defined' % name
        self.__RecordSet[name] = record

    def LookupRecord(self, record):
        '''Returns the record with the given name.  We perform record name
        expansion using the currently configured record name hook.'''
        return self.__RecordSet[recordnames.RecordNames.RecordName(record)]

    def Print(self):
        '''Output complete set of records to stdout.'''
        # Print the records in alphabetical order: gives the reader a fighting
        # chance to find their way around the generated database!
        for record in sorted(self.__RecordSet.keys()):
            self.__RecordSet[record].Print()

    def PrintAutosaves(self):
        '''Output all autosaves to stdout.'''
        for record in sorted(self.__RecordSet.keys()):
            self.__RecordSet[record].PrintAutosaves()

    def CountRecords(self):
        '''Returns the number of published records.'''
        return len(self.__RecordSet)

    def CountAutosaves(self):
        '''Returns the number of autosave entries.'''
        return sum(record.CountAutosaves()
            for record in self.__RecordSet.values())
            


        
class SubstitutionSet(Singleton):
    def __init__(self):
        self.Reset()

    def Reset(self):
        # Dictionary indexed by substitution sub-classes.  For each sub-class
        # the entry consists of a list of substitution instances.
        self.__Substitutions = {}
        

    def AddSubstitution(self, substitution):
        subClass = substitution.__class__
        if subClass not in self.__Substitutions:
            self.__Substitutions[subClass] = []
        self.__Substitutions[subClass].append(substitution)


    def ExpandSubstitutions(self, msiPath):
        '''Expand all the substitutions inline.  The path to locate the msi
        application used for expanding must be passed in.'''
        for subList in self.__Substitutions.values():
            for substitution in subList:
                substitution.ExpandSubstitution(msiPath)

    def SortedTemplateList(self):
        '''Returns a list of all current substitutions as a list of pairs
        (substitution_class, instance_list) sorted by the name of the
        template file associated with each subsitution class.'''
        return sorted(
            self.__Substitutions.items(),
            key=lambda (s,l): s.TemplateFile)

    def Print(self, macro_name = True):
        '''Prints out a substitutions file.'''
        # Print out the list in canonical order to help with comparison
        # across minor changes.
        for template, subList in self.SortedTemplateList():
            print
            print 'file %s' % template.TemplateName(macro_name)
            print '{'
            template.PrintPattern()
            for substitution in subList:
                substitution.PrintSubstitution()
            print '}'

    def CountSubstitutions(self):
        return len(self.__Substitutions)



class Substitution(ModuleBase):
    '''Each sub-class of this class defines a Substitution.  A Substitution is
    defined by specifying the following class members in the subclass:
        Arguments = (...)
            List of names of Substitution arguments that must be filled in when
            specifying a Substitution.
        TemplateFile = '...'
            Name of template file to be loaded.  By default this will be
            looked for in the db subdirectory of the library.
    '''

    BaseClass = True
    
    Arguments = ()
    TemplateFile = None

    @classmethod
    def TemplateName(cls, macro_name = False):
        '''Computes the template file name.  If macro_name is true then
        a form suitable for msi macro expansion is returned.'''
        return os.path.join(
            cls.LibPath(macro_name = macro_name), 'db', cls.TemplateFile)

    @classmethod
    def PrintPattern(cls):
        '''Outputs the substitution pattern line associated with this
        Substitution.  This is output in a format suitable for inclusion within
        a substitutions file.'''
        print 'pattern {', ', '.join(cls.Arguments), '}'
        

    def __init__(self, **args):
        '''Creates a substitution instance with the given arguments.  The
        arguments need to match the arguments expected by the template to
        be expanded.'''
        
        self.__super.__init__()
        
        # Check that all the required arguments have been given: we can't do
        # template expansion unless every argument is specified.
        assert set(args.keys()) == set(self.Arguments), \
            'Arguments missing or not recognised'
        # Check that the referenced template file actually exists!
        template = self.TemplateName()
        assert os.access(template, os.R_OK), \
            'Can\'t find template file "%s"' % template

        # Add ourself to the list of substitutions.
        self.args = args
        SubstitutionSet.AddSubstitution(self)


    def PrintSubstitution(self):
        '''Outputs a single substitution line, in order of arguments.  This
        should be preceded by a call to PrintPattern().'''
        print '    {', ', '.join(
            [QuoteArgument(self.args[arg]) for arg in self.Arguments]), \
            '}'

    def ExpandSubstitution(self, msiPath):
        '''Directly expand the substitution inline.'''
        
        argList = ['%s=%s' % (arg, QuoteArgument(self.args[arg]))
                   for arg in self.Arguments]
        template = self.TemplateName()

        print
        print '#', 75 * '-'
        print '# Template expansion for'
        print '# %s' % template
        print '#    %s' % ', '.join(argList)
        print '#', 75 * '-'
        print
        
        msi = [os.path.join(msiPath, 'msi')] + \
              ['-M%s' % arg for arg in argList] + [template]
        p = subprocess.Popen(msi, stdout=subprocess.PIPE)
        for line in p.stdout:
            print line,
        assert p.wait() == 0, 'Error running msi'

        

def QuoteArgument(argument):
    '''Converts a string into a form suitable for passing to the database
    expansion and substitution framework.'''
    # According to the msi documentation at
    #    http://www.aps.anl.gov/asd/controls/epics/EpicsDocumentation/
    #        ExtensionsManuals/msi/msi.html
    # it is enough to quote backquotes (and presumably backslashes).
    def QuoteChar(char):
        if char in '"\\':
            return '\\' + char
        else:
            return char
    return '"' + ''.join(map(QuoteChar, str(argument))) + '"'


        
# Publicly available methods.
PublishRecord = RecordSet.PublishRecord
LookupRecord = RecordSet.LookupRecord


# Special recordset reset.
def Reset():
    RecordSet.Reset()
    SubstitutionSet.Reset()
