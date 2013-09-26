#!/bin/env dls-python2.7

from optparse import OptionParser
import re
from iocbuilder.autosubst import populate_class, macro_desc_re

def print_template_macros():
    parser = OptionParser("""usage: %prog [options] <template-file>

Scan a template file for macros, and print the # % macro, lines for it""")
    parser.add_option(
        '-i', action='store_true', dest='inplace',
        help='Write the macro definitions at the top of the input file')

    # parse arguments
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error(
            'Incorrect number of arguments - '
            'you must supply one input file')

    # prepare the arguments
    template_filename = args[0]
    class cls:
        """Description of what this template does"""
        WarnMacros = False
        Arguments = None

    # call populate_class
    populate_class(cls, template_filename)

    # formatted the resulting macros
    out = """# %% macro, __doc__, %s
#
# Macros:
""" % cls.__doc__.replace("\n", "\n# ")
    for macro in cls.ArgInfo.required_names:
        out += "# %% macro, %s, %s\n" % (macro,
            cls.ArgInfo.descriptions[macro].desc.split("\n<type")[0])
    for i, macro in enumerate(cls.ArgInfo.default_names):
        out += "# %% macro, %s, %s (Default = %s)\n" % (macro,
            cls.ArgInfo.descriptions[macro].desc.split("\n<type")[0].split("(Default =")[0].rstrip(" "),
            cls.ArgInfo.default_values[i])
    for macro in cls.ArgInfo.optional_names:
        out += "# %% macro, %s, %s\n" % (macro,
            cls.ArgInfo.descriptions[macro].desc.split("\n<type")[0])
    out += "\n"

    # Either output macro or write them to file
    if options.inplace:
        template_text = open(template_filename).read()
        # Get rid of the "# Macros:" line that we might have put in
        template_text = re.sub(r"(\n#[ \t]*)*Macros\:[\t ]*",
            "", template_text, flags=re.MULTILINE)        
        # Now split on the macro descriptions. 
        # Note that we only use every third item to get rid of the captured
        # name and description fields from the macro_desc_re
        sections = macro_desc_re.split(template_text)[::3]
        # lstrip newlines to get rid of extra whitespace left behind from
        # the split on the macro descriptions
        out = sections[0] + out + "".join(l.lstrip("\n") for l in sections[1:])
        # Write it to file
        open(template_filename, "w").write(out)
        print "Done"
    else:
        print out

if __name__=="__main__":
    print_template_macros()
