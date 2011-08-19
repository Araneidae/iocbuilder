'''Collections of records.'''

import os.path
import subprocess

import recordnames
import libversion
import support
import paths


__all__ = ['LookupRecord', 'Substitution']



class RecordSet(support.Singleton):
    def __init__(self):
        self.Reset()

    def Reset(self):
        self.__RecordSet = {}
        self.__HeaderLines = []

    # Add a record to the list of records to be published.
    def PublishRecord(self, name, record):
        assert name not in self.__RecordSet, 'Record %s already defined' % name
        self.__RecordSet[name] = record

    # Returns the record with the given name.  We perform record name
    # expansion using the currently configured record name hook.
    def LookupRecord(self, record):
        return self.__RecordSet[recordnames.RecordNames.RecordName(record)]

    # Output complete set of records to stdout.
    def Print(self):
        for line in self.__HeaderLines:
            print line
        # Print the records in alphabetical order: gives the reader a fighting
        # chance to find their way around the generated database!
        for record in sorted(self.__RecordSet.keys()):
            self.__RecordSet[record].Print()

    # Returns the number of published records.
    def CountRecords(self):
        return len(self.__RecordSet)

    def AddHeaderLine(self, line):
        self.__HeaderLines.append(line)



class SubstitutionSet(support.autosuper):
    def __init__(self):
        # Dictionary indexed by substitution sub-classes.  For each sub-class
        # the entry consists of a list of substitution instances.
        #   We use an ordered dictionary so that we can print out
        # substitutions in the order they were originally given.
        self.__Substitutions = support.OrderedDict()

    # Erase all recorded substitution instances.
    def Reset(self):
        self.__Substitutions.clear()

    # Ensures that templates which are marked as being overwritten by this
    # template are generated first.  Unfortunately multiple templates which
    # update the same records really are used.
    def __AddOverwrites(self, substitution):
        for cls in substitution.SubstitutionOverwrites:
            self.__AddOverwrites(cls)
        # Note that we index the list by template name rather than class.
        # This allows substitutions to be subclassed without breaking their
        # dependencies.
        return self.__Substitutions.setdefault(
            substitution.TemplateName(True), [])

    def AddSubstitution(self, substitution):
        self.__AddOverwrites(substitution.__class__).append(substitution)

    # Expand all the substitutions inline.  The path to locate the msi
    # application used for expanding must be passed in.
    def ExpandSubstitutions(self):
        for subList in self.__Substitutions.values():
            for substitution in subList:
                substitution.ExpandSubstitution()

    # Prints out a substitutions file.
    def Print(self, macro_name = True):
        # Print out the list in canonical order to help with comparison
        # across minor changes.
        for template, subList in self.__Substitutions.items():
            if not subList:
                continue
            print
            if hasattr(subList[0], 'ArgInfo'):
                lines = []
                for x in subList[0].Arguments:
                    if x in subList[0].ArgInfo.descriptions:
                        a = subList[0].ArgInfo.descriptions[x]
                        lines.append((x, a.desc.split('\n')[0]))
                if lines:
                    format = '#  %%-%ds  %%s' % max([len(x[0]) for x in lines])
                    print '# Macros:'
                    print '\n'.join([format % l for l in lines])
            print 'file %s' % template
            print '{'
            subList[0]._PrintPattern()
            for substitution in subList:
                substitution._PrintSubstitution()
            print '}'

    def CountSubstitutions(self):
        return len(self.__Substitutions)

    def AllSubstitutions(self):
        l = []
        for template, subList in self.__Substitutions.items():
            l += subList
        return l

## Each sub-class of this class defines a Substitution.
#
# A Substitution is defined by specifying at least the following class members
# in the subclass:
#
# \param Arguments
#   List of names of Substitution arguments that must be filled in when
#   specifying a Substitution.
# \param TemplateFile
#   Name of template file to be loaded.  By default this will be
#   looked for in the db subdirectory of the library.
# \param SubstitutionOverwrites
#   Where definitions from one template override an earlier template it is
#   necessary to ensure that templates are loaded in a particular sequence.
#   This is done by setting this varible to a list of all templates which need
#   to be loaded before this one.
class Substitution(libversion.ModuleBase):
    def __init_meta__(cls, subclass):
        if cls.TemplateFile:
            cls.TemplateFiles.append(
                os.path.join(cls.LibPath(), 'db', cls.TemplateFile))


    BaseClass = True
    # List of all template files
    TemplateFiles = []

    ## This should be assigned to in a subclass to specify the template file.
    TemplateFile = None
    ## These are the arguments that any instance of the class will expect
    Arguments = None

    # Dependencies between substitutions.
    SubstitutionOverwrites = []

    TemplateDir = None
    SubstitutionSet = SubstitutionSet()
    TemplateDir = 'db'

    # Computes the template file name.  If macro_name is true then a form
    # suitable for msi macro expansion is returned.
    @classmethod
    def TemplateName(cls, macro_name):
        assert cls.TemplateFile is not None, 'No template file specified'
        if cls.TemplateDir is None:
            return cls.TemplateFile
        else:
            return os.path.join(
                cls.LibPath(macro_name = macro_name),
                cls.TemplateDir, cls.TemplateFile)

    # Outputs the substitution pattern line associated with this Substitution.
    # This is output in a format suitable for inclusion within a substitutions
    # file.
    @classmethod
    def _PrintPattern(cls):
        if cls.Arguments:
            print 'pattern {', ', '.join(cls.Arguments), '}'


    ## Creates a substitution instance with the given arguments.  The
    # arguments need to match the arguments expected by the template to
    # be expanded.
    def __init__(self, **args):
        self.__super.__init__()

        # If we have Defaults, then update the argdict with them
        if hasattr(self, 'Defaults'):
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


    # Outputs a single substitution line, in order of arguments.  This should
    # be preceded by a call to _PrintPattern().
    def _PrintSubstitution(self):
        if self.Arguments:
            print '    {', ', '.join(
                [QuoteArgument(self.args[arg]) for arg in self.Arguments]), \
                '}'
        else:
            # Work around msi bug if no arguments given!
            print '    { _ }'

    # Directly expand the substitution inline.
    def ExpandSubstitution(self):
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

        if paths.msiPath:
            runMsi = os.path.join(paths.msiPath, 'msi')
        else:
            runMsi = 'msi'
        msi = [runMsi] + ['-M%s' % arg for arg in argList] + [template]
        p = subprocess.Popen(msi, stdout=subprocess.PIPE)
        for line in p.stdout:
            print line,
        assert p.wait() == 0, 'Error running msi'


RecordsSubstitutionSet = Substitution.SubstitutionSet
AllSubstitutions = RecordsSubstitutionSet.AllSubstitutions


# Converts a string into a form suitable for passing to the database expansion
# and substitution framework.
def QuoteArgument(argument):
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
