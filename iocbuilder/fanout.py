'''Support for creating fanout records.'''

from dbd import records
from recordbase import PP
import support


__all__ = ['create_fanout', 'create_dfanout']



# ----------------------------------------------------------------------------
#  Fanout record generation


# Support routine to do the work of fanout generation common to fanout and
# dfanout.
def _fanout_helper(
    fanout_name, link_list, fanout_size,
    record_factory, field_name, fixup_link, firstargs, nextargs):

    # First break the list of links into chunks small enough for each fanout
    # record.  First chop it into segments small enough to fit into each
    # fanout record, leaving room for an extra link.  The last record can take
    # an extra entry so then fix up the chopped list.
    chopped = support.choplist(link_list, fanout_size - 1)
    if len(chopped) > 1 and len(chopped[-1]) == 1:
        chopped[-2:] = [chopped[-2] + chopped[-1]]

    # Convert the chopped list into a list of fanout records.
    recordList = []
    args = firstargs
    for i, links in enumerate(chopped):
        # The first record gets the standard name and a different set of
        # record arguments.
        name = fanout_name
        if i > 0:
            name += str(i)
        # Build a fanout record with the computed name and arguments.
        record = record_factory(name, **args)
        args = nextargs     # Subsequent records get the other arguments
        # Link the new fanout record to the given list of links
        for i, link in enumerate(links):
            setattr(record, field_name(i), link)
        recordList.append(record)

    # Chain the fanout records together using the last field in each record:
    # we've taken care to reserve this field when we split the link list!
    next_name = field_name(fanout_size - 1)
    for prev, next in zip(recordList[:-1], recordList[1:]):
        setattr(prev, next_name, fixup_link(next))

    return recordList



## Creates one or more fanout records (as necessary) to fan processing out to
# a list of records.  If no more than 6 records are given then this creates a
# single fanout record called \c name.  Otherwise, further records are created
# and daisy-chained together: subsequent records are numbered in sequence.
#
# \param name
#   Name of first fanout record.  Subsequent records have a sequence number
#   appended to this name.
# \param *record_list
#   List of records to be processed.
# \param **args
#   Extra field definitions to be passed to the generated fanout records.
def create_fanout(name, *record_list, **args):
    # We can only support fanout to "All" style fanout records: to generate
    # masked or selected fanouts we'd need to create a cluster of supporting
    # calc records and structure the set rather differently.
    args['SELM'] = 'All'

    # All records after the first must be passive.
    firstargs = args
    nextargs = args.copy()
    nextargs['SCAN'] = 'Passive'
    if nextargs.has_key('PINI'):  del nextargs['PINI']

    def fieldname(i):   return 'LNK%d' % (i + 1)
    def identity(x):    return x
    record_list = _fanout_helper(
        name, record_list, 6, records.fanout, fieldname,
        identity, firstargs, nextargs)
    return record_list[0]


## Creates one or more data fanout records (as necessary) to fan a data output
# out to a list of records.  If no more than 8 records are given then this
# creates a single dfanout record called \c name.  Otherwise, further records
# are created and daisy-chained together: subsequent records are numbered in
# sequence.
#
# \param name
#   Name of first fanout record.  Subsequent records have a sequence number
#   appended to this name.
# \param *record_list
#   List of records to be processed.
# \param **args
#   Extra field definitions to be passed to the generated fanout records.
def create_dfanout(name, *record_list, **args):
    # All records after the first argument must operate passively and in
    # supervisory mode as they are simply mirroring the first record.
    firstargs = args
    nextargs = args.copy()
    nextargs.update(dict(SCAN = 'Passive', OMSL = 'supervisory'))
    if nextargs.has_key('DOL'):   del nextargs['DOL']
    if nextargs.has_key('PINI'):  del nextargs['PINI']

    def fieldname(i):   return 'OUT%c' % (ord('A') + i)
    record_list = _fanout_helper(
        name, record_list, 8, records.dfanout, fieldname,
        PP, firstargs, nextargs)
    return record_list[0]
