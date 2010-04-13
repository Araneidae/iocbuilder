# IOC initialisation support code

import os.path
import subprocess

import recordnames
import libversion
import support


__all__ = ['LookupRecord', 'Substitution']



class RecordSet(support.Singleton):
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

    def CountRecords(self):
        '''Returns the number of published records.'''
        return len(self.__RecordSet)            



class SubstitutionSet(support.autosuper_object):
    def __init__(self):
        # Dictionary indexed by substitution sub-classes.  For each sub-class
        # the entry consists of a list of substitution instances.
        #   We use an ordered dictionary so that we can print out
        # substitutions in the order they were originally given.
        self.__Substitutions = support.OrderedDict()

    def Reset(self):
        '''Erase all recorded substitution instances.'''
        self.__Substitutions.clear()

    def AddSubstitution(self, substitution):
        self.__Substitutions.setdefault(
            substitution.TemplateName(True), []).append(substitution)

    def ExpandSubstitutions(self, msiPath):
        '''Expand all the substitutions inline.  The path to locate the msi
        application used for expanding must be passed in.'''
        for subList in self.__Substitutions.values():
            for substitution in subList:
                substitution.ExpandSubstitution(msiPath)

    def Print(self, macro_name = True):
        '''Prints out a substitutions file.'''
        # Print out the list in canonical order to help with comparison
        # across minor changes.
        for template, subList in self.__Substitutions.items():
            print
            print 'file %s' % template
            print '{'
            subList[0]._PrintPattern()
            for substitution in subList:
                substitution._PrintSubstitution()
            print '}'

    def CountSubstitutions(self):
        return len(self.__Substitutions)


class Substitution(libversion.ModuleBase):
    '''Each sub-class of this class defines a Substitution.  A Substitution is
    defined by specifying the following class members in the subclass:
        Arguments = (...)
            List of names of Substitution arguments that must be filled in when
            specifying a Substitution.
        TemplateFile = '...'
            Name of template file to be loaded.  By default this will be
            looked for in the db subdirectory of the library.
    '''

    def __init_meta__(cls, subclass):
        if cls.TemplateFile:
            cls.TemplateFiles.append(cls.TemplateFile)
        

    BaseClass = True
    TemplateFile = None
    TemplateFiles = []
    TemplateDir = None
    SubstitutionSet = SubstitutionSet()
    TemplateDir = 'db'   
    ## These are the arguments that any instance of the class will expect
    Arguments = None

    def TemplateName(self, macro_name):
        '''Computes the template file name.  If macro_name is true then
        a form suitable for msi macro expansion is returned.'''
        assert self.TemplateFile is not None, 'No template file specified'
        if self.TemplateDir is None:
            return self.TemplateFile
        else:
            return os.path.join(
                self.LibPath(macro_name = macro_name),
                self.TemplateDir, self.TemplateFile)

    @classmethod
    def _PrintPattern(cls):
        '''Outputs the substitution pattern line associated with this
        Substitution.  This is output in a format suitable for inclusion within
        a substitutions file.'''
        if cls.Arguments:
            print 'pattern {', ', '.join(cls.Arguments), '}'
        

    def __init__(self, **args):
        '''Creates a substitution instance with the given arguments.  The
        arguments need to match the arguments expected by the template to
        be expanded.'''
        self.__super.__init__()
        
        # If we have Defaults, then update the argdict with them
        if hasattr(self, "Defaults"):
            args = dict(self.Defaults, **args)
        
        # Check that all the required arguments have been given: we can't do
        # template expansion unless every argument is specified.
        assert self.TemplateFile, 'Must specify template file'
        assert self.Arguments is not None, 'Must specify some Arguments'
        assert set(args) == set(self.Arguments), \
            'Arguments %s missing or not recognised' % \
                list(set(args).symmetric_difference(set(self.Arguments)))
        # Check that the referenced template file actually exists!
        template = self.TemplateName(False)
        if self.TemplateDir is not None:
            assert os.access(template, os.R_OK), \
                'Can\'t find template file "%s"' % template
        else:
            print 'Not validating template file "%s"' % template

        # Add ourself to the list of substitutions.
        self.args = args
        if self.SubstitutionSet is not None:
            self.SubstitutionSet.AddSubstitution(self)


    def _PrintSubstitution(self):
        '''Outputs a single substitution line, in order of arguments.  This
        should be preceded by a call to _PrintPattern().'''
        if self.Arguments:
            print '    {', ', '.join(
                [QuoteArgument(self.args[arg]) for arg in self.Arguments]), \
                '}'
        else:
            # Work around msi bug if no arguments given!
            print '    { _ }'

    def ExpandSubstitution(self, msiPath):
        '''Directly expand the substitution inline.'''
        
        argList = ['%s=%s' % (arg, QuoteArgument(self.args[arg]))
                   for arg in self.Arguments]
        template = self.TemplateName(False)

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
        

RecordsSubstitutionSet = Substitution.SubstitutionSet


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
    RecordsSubstitutionSet.Reset()
