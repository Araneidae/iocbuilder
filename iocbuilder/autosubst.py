'''AutoSubstitution for scanning template files.'''

from libversion import ModuleBase, modules, PythonIdentifier
import os, re, sys
import recordset
from arginfo import *

__all__ = ['AutoSubstitution']

# This iterator will find any $(...) macro in line. The number of ( brackets
# ) and brackets in the expression will match
def find_macros(line):
    bracket = 0
    i = 0
    macro = ''

    while i < len(line):
        if bracket > 0:
            # we're in a macro
            match = bracket_open.match(line, i)
            if match:
                # we've opened another bracket
                bracket += 1
            else:
                # we've closed a bracket
                match = bracket_close.match(line, i)
                bracket -= 1
            if bracket == 0:
                # we've closed the macro bracket
                yield macro
                macro = ''
                i += 1
            else:
                # we've closed a non-macro bracket
                macro += match.groups()[0]
                i = match.end()
        else:
            # we're not in a macro, find the start of the next one
            match = macro_start.search(line, i)
            if match:
                i = match.end()
                macro += match.groups()[0]
                bracket = 1
            else:
                i = len(line)

def populate_class(cls, template_file):
    '''Returns list of keys and dictionary of defaults.'''
    text = open(template_file).read()
    required_names = []
    default_names = []
    default_values = []
    optional_names = []
    Obs = {}
    doc = ''
    for line in text.splitlines():
        # find all macro names
        for mtext in find_macros(line):
            if '=' in mtext:
                # this a macro with a default value
                mtext, default = mtext.split('=', 1)
                # check it's not a required value
                assert mtext not in required_names + optional_names, \
                    'Cannot define default macro "%s", already defined as '\
                    'a non-default macro in "%s"' % (mtext, template_file)
                if mtext in default_names:
                    # if it's a default value already, check it matches
                    old_default = default_values[default_names.index(mtext)]
                    assert default == old_default, \
                        'Cannot set macro "%s" to "%s", already defined with '\
                        'value "%s" in "%s"' % (mtext, default, \
                            old_default, template_file)
                else:
                    # add it as a default value
                    default_names.append(mtext)
                    default_values.append(default)
            else:
                # this is a required or optional macro
                # strip off any msi ,undefined stuff
                if mtext.endswith(',undefined'):
                    mtext = mtext.replace(',undefined', '')
                assert mtext not in default_names, \
                    'Cannot define macro "%s", already defined as '\
                    'a default macro in "%s"' % (mtext, template_file)
                if line.startswith('#'):
                    # comments are optional if they are epics_parser lines
                    if epics_parser_re.match(line):
                        if mtext not in optional_names:
                            optional_names.append(mtext)
                else:
                    if mtext not in required_names:
                        required_names.append(mtext)

    # Find # % gui tags and store them in cls.guiTags.
    cls.guiTags = gui_re.findall(text)

    # find all the descriptions for ArgInfo objects
    def add_ob(name, ob):
        Obs[name] = ob
        for l in (required_names, default_names, optional_names):
            if name in l:
                # shift it to the end
                if l is default_names:
                    default_values.append(
                        default_values.pop(default_names.index(name)))
                l.append(l.pop(l.index(name)))


    for name, desc in macro_desc_re.findall(text):
        search = re.search(r'\n#[ \t]*', desc)
        if search:
            desc = re.sub(search.group(), '\n', desc)
        # a __doc__ macro is the docstring for the object
        if name == '__doc__':
            doc = desc
        elif name in required_names + default_names + optional_names:
            add_ob(name, Simple(desc))
        elif cls.WarnMacros:
            print >> sys.stderr, \
                '***Warning: Describing non-existent macro "%s" in "%s"' % \
                    (name, template_file)
    for name in required_names + default_names + optional_names:
        if name not in Obs:
            if cls.WarnMacros:
                print >> sys.stderr, \
                    '***Warning: Undescribed macro "%s" in "%s"' % \
                    (name, template_file)
            add_ob(name, Simple('Template argument'))
    # make sure optional_names aren't also required names
    optional_names = [x for x in optional_names if x not in required_names]

    # Create all the important attributes we need if they're not already
    # given.

    # store the docstring
    if doc:
        cls.__doc__ = doc
    # create Arguments
    if cls.Arguments is None:
        cls.Arguments = required_names + default_names + optional_names
    # create Defaults
    if not hasattr(cls, 'Defaults'):
        cls.Defaults = dict(zip(
            default_names + optional_names,
            default_values + ['' for x in optional_names]))

    # create ArgInfo
    if not hasattr(cls, 'ArgInfo'):
        cls.ArgInfo = makeArgInfo(**Obs)
        cls.ArgInfo.default_names = default_names
        cls.ArgInfo.default_values = default_values
        cls.ArgInfo.required_names = required_names
        cls.ArgInfo.optional_names = optional_names


## Subclass of Substitution that scans its template file to find the macros it
# uses, and creates an ArgInfo object from them.
class AutoSubstitution(recordset.Substitution):
    BaseClass = True
    ## Set this to False to supress warnings on undescribed macros
    WarnMacros = True
    ## This is set to True to disable scanning of the template file in
    # other subclasses of this
    Scanned = False

    def __init_meta__(cls, first_call):
        if cls.TemplateFile is not None and not cls.Scanned:
            # populate Arguments, Descriptions etc.
            populate_class(cls, cls.ModuleFile(
                os.path.join('db', cls.TemplateFile)))
            cls.Scanned = True


    @classmethod
    def fromModuleVersion(cls, moduleVersion):
        '''Make autosubstitution objects for all files in the db dir
        of moduleVersion object'''
        path = os.path.join(moduleVersion.LibPath(), 'db')
        if os.path.isdir(path):
            # for each db file
            for db in os.listdir(path):
                # make sure it is a template or db
                if not (db.endswith('.template') or db.endswith('.db')):
                    continue
                # make sure we haven't already made a custom builder object
                # for it
                if os.path.join(path, db) in cls.TemplateFiles:
                    continue
                # make an autoSubstitution for it
                clsname = PythonIdentifier('auto_' + db.split('.')[0])
                class temp(AutoSubstitution):
                    WarnMacros = False
                    ModuleName = moduleVersion.Name()
                    TemplateFile = db
                    TrueName = clsname
                setattr(moduleVersion.module, clsname, temp)

# This re matches an line like #% autosave 1 or # % gda_tag, template, ...
epics_parser_re = re.compile(r'^#[ \t]*%')

# This re matches the $( msi syntax until the first ) or (
macro_start = re.compile(r'\$\(([^\(\)]*)')

# This re matches a ( until the next ) or (
bracket_open = re.compile(r'(\([^\(\)]*)')

# This re matches a ) until the next ) or (
bracket_close = re.compile(r'(\)[^\(\)]*)')

# This re matches and gui tags
gui_re = re.compile(r'#[ \t]*%[ \t]*gui[ \t]*,[ \t]*(.*)')

# This re matches a macro description line like #% macro, P, Pv Prefix.
# It will also match multiline descriptions like:
#% macro, P, Pv Prefix with
# a very long macro
# A description is terminated by a 'blank' line which may optionally contain
# a hash and multiple spaces or tabs.
macro_desc_re = re.compile(
    r'^#[ \t]*%[ \t]*macro[ \t]*,[ \t]*' # This is the #% macro, prefix
    r'([^, \t]+)[ \t]*,[ \t]*' # Captures the macro name and discards comma
    r'([^\n]+' # This start the description capture and the first line
    r'(?:\n#[ \t]*[^\n \t%#][^\n]*)*)', # subsequent non-'blank' line
    re.MULTILINE)
